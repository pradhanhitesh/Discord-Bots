import base64

class MIMEMessage:
    def __init__(sel):
        pass
    
    def _mime_type(self, message):
        return message['payload']['mimeType']
    
    def _decode_data(self, data):
        if not isinstance(data, str):
            raise TypeError(f"Expected base64-encoded string, got {type(data).__name__}")
        
        try:
            # Decode base64
            byte_code = base64.urlsafe_b64decode(data)
            if not isinstance(byte_code, (bytes, bytearray)):
                raise TypeError("Decoded data is not a bytes-like object")

            # Decode UTF-8
            text = byte_code.decode("utf-8")
            return text

        except (base64.binascii.Error, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to decode message: {e}")
        
    def _collect_metadata(self, message):
        metadata = {}
        try: 
            for value in message['payload']['headers']:
                if value.get('name') == 'From':
                    metadata['From'] = value.get('value')
                elif value.get('name') == 'To':
                    metadata['To'] = value.get('value')
                elif value.get('name') == 'Subject':
                    metadata['Subject'] = value.get('value')

            return metadata
        except Exception as e:
            raise ValueError(f"Metadata could not be extracted from Message due to {e}")
        
        
    def _mime_text_plain(self, message):
        if self._mime_type(message) != 'text/plain':
            raise ValueError(f"Message is not of type text/plain. Instead got {self._mime_type(message)}")
        
        try:
            data = message['payload']['body']['data']
            return self._decode_data(data)
        except Exception as e:
            raise ValueError(f"Failed to decode message: {e}")

    def _mime_text_html(self, message):
        if self._mime_type(message) != 'text/html':
            raise ValueError(f"Message is not of type text/html. Instead got {self._mime_type(message)}")
        
        try:
            data = message['payload']['body']['data']
            return self._decode_data(data)
        except Exception as e:
            raise ValueError(f"Failed to decode message: {e}")

    def _mime_multipart_alternative(self, message, extract='text/plain'):
        if self._mime_type(message) != 'multipart/alternative':
            raise ValueError(f"Message is not of type multipart/alternative. Instead got {self._mime_type(message)}")
        
        try:
            for part in message['payload']['parts']:
                if extract == 'text/plain':
                    data = part['body']['data']
                    return self._decode_data(data)
                elif extract == 'text/html':
                    data = part['body']['data']
                    return self._decode_data(data)
        except Exception as e:
            raise ValueError(f"Failed to decode message: {e}")

    def _mime_multipart_mixed(self, message, extract='text/plain'):
        if self._mime_type(message) != 'multipart/mixed':
            raise ValueError(f"Message is not of type multipart/mixed. Instead got {self._mime_type(message)}")

        try:
            for part in message['payload']['parts'][0]['parts']:
                if extract == 'text/plain':
                    data = part['body']['data']
                    return self._decode_data(data)
                elif extract == 'text/html':
                    data = part['body']['data']
                    return self._decode_data(data)
        except Exception as e:
            raise ValueError(f"Failed to decode message: {e}")


    def _mime_multipart_related(self, message, extract='text/plain'):
        if self._mime_type(message) != 'multipart/related':
            raise ValueError(f"Message is not of type multipart/related. Instead got {self._mime_type(message)}")

        try:
            for part in message['payload']['parts'][0]['parts']:
                if extract == 'text/plain':
                    data = part['body']['data']
                    return self._decode_data(data)
                elif extract == 'text/html':
                    data = part['body']['data']
                    return self._decode_data(data)
        except Exception as e:
            raise ValueError(f"Failed to decode message: {e}")

    def _extract_content(self, message):
        mime_type = self._mime_type(message)

        if mime_type == 'text/html':
            return self._mime_text_html(message)
        elif mime_type == 'text/plain':
            return self._mime_text_plain(message)
        elif mime_type == 'multipart/alternative':
            return self._mime_multipart_alternative(message)
        elif mime_type == 'multipart/mixed':
            return self._mime_multipart_mixed(message)
        elif mime_type == 'multipart/related':
            return self._mime_multipart_related(message)
        else:
            raise ValueError(f"Unsupported MIME type: {mime_type}")