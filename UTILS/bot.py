from googleapiclient.discovery import build
from google import genai
from google.genai import types
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from typing import Optional
from jinja2 import Template
from weasyprint import HTML
from datetime import datetime
from UTILS.mail import MIMEMessage
import re
import json
import os
import pytz
import html

load_dotenv()

class PhDBot:
    def __init__(self):
        pass

    def _gmail(self, GMAIL_TOKEN: dict, search_query: str):
        # Sanity checks
        if not isinstance(GMAIL_TOKEN, str):
            raise ValueError(f"GMAIL_TOKEN expects a dictionary (parsed JSON). Instead got {type(GMAIL_TOKEN).__name__}")

        # If modifying these scopes, delete the file token.json
        # And generate token.json again using generate_tokens.py
        SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
        creds = Credentials.from_authorized_user_info(json.loads(GMAIL_TOKEN), SCOPES)

        # Get messages
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId='me', q=search_query).execute()
        messages = results.get('messages',[]);

        # Extract content from messages
        messages_data = {}
        for _, message in enumerate(messages):
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            try:
                content = MIMEMessage()._extract_content(message=msg)
                meta = MIMEMessage()._collect_metadata(message=msg)
                messages_data[message['id']] = {"metadata": meta, "message": content}
            except Exception as e:
                print(f"Unable to retireve message ID: {message['id']} due to error: {e}")
                continue

        return messages_data

    def _llm(self, GEMINI_API_KEY: str, messages_data: dict, sys_instruct: str):
        # Setup client
        client = genai.Client(api_key=GEMINI_API_KEY)

        message_summary = {}
        for message in messages_data:
            content = messages_data[message]['message']
            response = client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                max_output_tokens=500,
                temperature=0.1),
                contents=[content],)
            
            if "```json" in response.text:
                # Clean the response by removing the code block markers
                response_content_cleaned = response.text.replace("```json", "").replace("```", "").strip()
                response_json = json.loads(response_content_cleaned)
            else:
                # Parse the response content back to a Python dictionary
                response_json = json.loads(response.text)

            message_summary[message] = response_json

        return message_summary

    def _message(self, messages_data: dict, message_summary: dict):
        # List of messages to send
        to_send = []
        for message in message_summary:
            # content = [f"# Message ID: {message}\n"]
            if message_summary[message]['condition']:
                from_field = messages_data[message]['metadata']['From']
                subject = messages_data[message]['metadata']['Subject']
                date = messages_data[message]['metadata']['Date']
                summary = message_summary[message]['summary']

                content = []
                content.append(f"### 📝 **Subject:** {subject}\n")
                content.append(f"### **Date:** {date}\n")
                content.append(f"### Message from {from_field}\n")
                content.append(f"**Summary:** {summary}")
                to_send.append("".join(content))

        return to_send

class OpedTH:
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
    
    def _extract_paragraph(self, soup, GEMINI_API_KEY: str, summarize=True):
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

        if summarize:
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
        else:
            return body_content, ""

    def _process_page(self, soup: BeautifulSoup, GEMINI_API_KEY: str, output_path: Optional[str] = None, output_md=True, summarize=True):
        if output_path != None:
            if not os.path.exists(output_path):
                raise ValueError(f"Specified path {output_path} does not exist.")
        
        # Assuming _collect_metadata and _extract_paragraph are defined elsewhere
        metadata = self._collect_metadata(soup)
        content, summary = self._extract_paragraph(soup, GEMINI_API_KEY, summarize=summarize)

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
    
class OpedDH():
    def __init__(self):
        pass


    def _collect_metadata(self, soup):
        # Initialize default values to avoid UnboundLocalError
        headline = "N/A"
        publish_date = "N/A"
        publish_time = "N/A"

        try:
            # Find all JSON-LD script tags
            json_scripts = soup.find_all("script", type="application/ld+json")

            for script in json_scripts:
                script_data = json.loads(script.string)

                if 'headline' in script_data and 'datePublished' in script_data:
                    headline = script_data['headline']
                    publication_datetime = script_data['datePublished']
                    dt_obj = datetime.fromisoformat(publication_datetime)
                    publish_date = dt_obj.strftime("%d-%m-%Y")
                    publish_time = dt_obj.strftime("%H:%M")
                    break

        except Exception as e:
            print(f"Error parsing metadata: {e}")

        # Return metadata even if parsing fails
        return {
            "Headline": headline,
            "Publication Date": publish_date,
            "Publication Time": publish_time
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
    
    def _extract_paragraph(self, soup, GEMINI_API_KEY: str, summarize=True):
        json_script = soup.find_all("script", type="application/ld+json")[1]
        json_script = json.loads(json_script.string)

        article_body = html.unescape(json_script.get('articleBody'))

        # Parse with BeautifulSoup
        soup = BeautifulSoup(article_body, "html.parser")

        # Extract text from all <p class="bodytext"> elements
        body_content = " ".join(p.get_text() for p in soup.find_all("p"))

        if summarize:
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
        else:
            return body_content, ""
    
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
