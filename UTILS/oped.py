import re
from bs4 import BeautifulSoup
import json
import os
from typing import Optional
from google import genai
from google.genai import types
from jinja2 import Template
from weasyprint import HTML
from datetime import datetime
import pytz

class Oped():
    def __init__(self):
        pass

    def _collect_metadata(self, soup):
        # Extract headline from <meta> tag
        headline = soup.find("meta", attrs={"name": "title"})
        headline = headline["content"] if headline else "N/A"

        # Extract publish date from <meta> tag
        publish_date = soup.find("meta", attrs={"name": "publish-date"})
        publish_date = publish_date["content"][:10] if publish_date else "N/A"

        # Extract publish time from <meta> tag
        publish_time = soup.find("meta", attrs={"name": "publish-date"})
        publish_time = publish_time["content"][11:16] if publish_time else "N/A"

        # Try extracting from JavaScript (dataLayer) if available
        script_tag = soup.find("script", string=re.compile("dataLayer"))
        if script_tag:
            match = re.search(r"dataLayer\.push\((.*?)\);", script_tag.string, re.DOTALL)
            if match:
                try:
                    data_layer = json.loads(match.group(1).replace("'", '"'))  # Convert JS-like to JSON
                    page_details = data_layer.get("pageDetails", {})
                    
                    headline = page_details.get("headline", headline)
                    publish_date = page_details.get("publishDate", publish_date)
                    publish_time = page_details.get("publishTime", publish_time)
                except json.JSONDecodeError:
                    pass

        return {
                "Headline" : headline,
                "Publication Date": publish_date,
                "Publication Time": publish_time,
                }
    
    def _llm(self, GEMINI_API_KEY: str, content: str, sys_instruct: str):
        # Setup client
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=sys_instruct),
            contents=[content])
        
        if "```json" in response.text:
            # Clean the response by removing the code block markers
            response_content_cleaned = response.text.replace("```json", "").replace("```", "").strip()
            response_json = json.loads(response_content_cleaned, strict=False)
        else:
            # Parse the response content back to a Python dictionary
            response_json = json.loads(response.text, strict=False)

        return response_json
    
    def _extract_paragraph(self, soup, GEMINI_API_KEY: str):
        # Initialize list
        body_content = []

        # Find the tag with itemprop="articleBody"
        article_body = soup.find(attrs={"itemprop": "articleBody"})

        # If the article body exists, find all <p> tags within it
        if article_body:
            paragraphs = article_body.find_all('p', recursive=False)

            # Print the text of each paragraph
            for i, p in enumerate(paragraphs, 1):
                if 'Published - ' not in p.text.strip():
                    body_content.append(p.text.strip())
                else:
                    body_content.append(p.text.strip())
                    break
        else:
            print("No article body found with itemprop='articleBody'.")

        body_content = " ".join(content for content in body_content)

        # Summarize content
        sys_instruct="""
        Here are your strict instructions:
        You are an AI specializing in summarizing content, particularly Op-Ed news articles.  
        Your task is to condense the provided text into a concise and informative summary of exactly 100 words.  
        Focus on capturing the key arguments, main points, and essential details of the original article while preserving its core essence.  Avoid adding any personal opinions or interpretations.  
        Maintain the original meaning and tone of the source material.

        Use this JSON schema:
        Summary = {'summary': str}
        Return: dict[Summary]

        """
        content = self._llm(GEMINI_API_KEY, body_content, sys_instruct)

        return body_content, content['summary']


    def _process_page(self, soup: BeautifulSoup, GEMINI_API_KEY: str, output_path: Optional[str] = None, output_md=True):
        if output_path != None:
            if not os.path.exists(output_path):
                raise ValueError(f"Specified path {output_path} does not exist.")
        
        # Assuming _collect_metadata and _extract_paragraph are defined elsewhere
        metadata = self._collect_metadata(soup)
        content, summary = self._extract_paragraph(soup, GEMINI_API_KEY)

        # Store data in dict
        page_data = {
                "Metadata" : metadata,
                "Content" : {
                    "Original" : content,
                    "Summary" : summary
                }
            }
        
        try:
            if output_md and not output_path:
                return page_data       
            elif output_md and output_path:
                filename = metadata.get("Headline",["No Headline"]).replace(" ","+")
                output_path = os.path.join(output_path, f"{filename}.json")
                with open(output_path, 'w') as file:
                    json.dump(page_data, file)
                return page_data
        except Exception as e:
            raise ValueError(f"Could not extract page data due to {e}")
        
    def _message(self, page_data: dict, template_path: str, output_path: str):
        message_content = []

        # MD message
        for meta in page_data['Metadata']:
            message_content.append(f"### **{meta}:** {page_data['Metadata'][meta]}\n")
        message_content.append(f"**Summary:** {page_data['Content']['Summary']}")
        message_content = "".join(content for content in message_content)

        # PDF file
        template_vars = {
            'headline': page_data['Metadata']['Headline'],
            'publication_date' : page_data['Metadata']['Publication Date'],
            'publication_time' : page_data['Metadata']['Publication Time'],
            'original' : page_data['Content']['Original'],
            'summary': page_data['Content']['Summary'],
            'generation_date' : datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %H:%M')
        }

        # Read the template file directly
        with open(template_path, 'r') as file:
            template_content = file.read()
        
        # Render the template with the provided context
        template = Template(template_content)
        html_content = template.render(template_vars)

        # Convert the rendered HTML to a PDF
        output_path = os.path.join(output_path, f"{page_data['Metadata']['Headline'].replace(' ','+')}.pdf")
        HTML(string=html_content).write_pdf(output_path)

        return message_content, output_path