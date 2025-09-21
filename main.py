import xml.etree.ElementTree as ET
import os
import base64
import re
import sys
from pathlib import Path

class RBXLXParser:
    def __init__(self):
        self.script_types = {"Script", "LocalScript", "ModuleScript"}
        self.output_dir = None
        
    def sanitize_filename(self, name):
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = name.rstrip('. ')
        return name if name else "unnamed"
    
    def get_script_extension(self, class_name):
        extensions = {
            "Script": ".server.lua",
            "LocalScript": ".local.lua", 
            "ModuleScript": ".module.lua"
        }
        return extensions.get(class_name, ".lua")
    
    def get_model_extension(self, class_name):
        return f".{class_name.lower()}.model"
    
    def decode_protected_string(self, protected_string):
        try:
            if protected_string.startswith('<![CDATA[') and protected_string.endswith(']]>'):
                return protected_string[9:-3]
            return protected_string
        except:
            return protected_string
    
    def extract_properties(self, item_element):
        properties = {}
        props_element = item_element.find('Properties')
        
        if props_element is not None:
            for prop in props_element:
                prop_name = prop.get('name', 'unknown')
                prop_type = prop.tag
                
                if prop_type == 'string':
                    properties[prop_name] = prop.text or ""
                elif prop_type == 'bool':
                    properties[prop_name] = prop.text == 'true'
                elif prop_type in ['int', 'int64']:
                    try:
                        properties[prop_name] = int(prop.text or 0)
                    except:
                        properties[prop_name] = 0
                elif prop_type == 'float':
                    try:
                        properties[prop_name] = float(prop.text or 0)
                    except:
                        properties[prop_name] = 0.0
                elif prop_type == 'Vector3':
                    x = prop.find('X')
                    y = prop.find('Y') 
                    z = prop.find('Z')
                    properties[prop_name] = {
                        'X': float(x.text) if x is not None else 0,
                        'Y': float(y.text) if y is not None else 0,
                        'Z': float(z.text) if z is not None else 0
                    }
                elif prop_type == 'Color3':
                    r = prop.find('R')
                    g = prop.find('G')
                    b = prop.find('B')
                    properties[prop_name] = {
                        'R': float(r.text) if r is not None else 0,
                        'G': float(g.text) if g is not None else 0,
                        'B': float(b.text) if b is not None else 0
                    }
                elif prop_type == 'UDim2':
                    xs = prop.find('XS')
                    xo = prop.find('XO')
                    ys = prop.find('YS')
                    yo = prop.find('YO')
                    properties[prop_name] = {
                        'XS': float(xs.text) if xs is not None else 0,
                        'XO': float(xo.text) if xo is not None else 0,
                        'YS': float(ys.text) if ys is not None else 0,
                        'YO': float(yo.text) if yo is not None else 0
                    }
                elif prop_type == 'CoordinateFrame':
                    x = prop.find('X')
                    y = prop.find('Y')
                    z = prop.find('Z')
                    r00 = prop.find('R00')
                    r01 = prop.find('R01')
                    properties[prop_name] = {
                        'Position': {
                            'X': float(x.text) if x is not None else 0,
                            'Y': float(y.text) if y is not None else 0,
                            'Z': float(z.text) if z is not None else 0
                        },
                        'R00': float(r00.text) if r00 is not None else 1,
                        'R01': float(r01.text) if r01 is not None else 0
                    }
                else:
                    properties[prop_name] = prop.text or ""
                    
        return properties
    
    def process_item(self, item_element, current_path="game"):
        class_name = item_element.get('class', 'Unknown')
        
        name = "Unnamed"
        props_element = item_element.find('Properties')
        if props_element is not None:
            name_element = props_element.find('.//string[@name="Name"]')
            if name_element is not None and name_element.text:
                name = name_element.text
        
        sanitized_name = self.sanitize_filename(name)
        
        if current_path == "game":
            item_path = os.path.join(self.output_dir, sanitized_name)
        else:
            item_path = os.path.join(current_path, sanitized_name)
        
        if class_name in self.script_types:
            self.create_script_file(item_element, current_path, sanitized_name, class_name)
        else:
            self.create_model_file(item_element, current_path, sanitized_name, class_name)
            
            children = item_element.findall('Item')
            if children:
                os.makedirs(item_path, exist_ok=True)
                
                for child in children:
                    self.process_item(child, item_path)
    
    def create_script_file(self, item_element, current_path, name, class_name):
        props_element = item_element.find('Properties')
        source_code = ""
        
        if props_element is not None:
            source_element = props_element.find('.//ProtectedString[@name="Source"]')
            if source_element is not None and source_element.text:
                source_code = self.decode_protected_string(source_element.text)
        
        extension = self.get_script_extension(class_name)
        filename = f"{name}{extension}"
        filepath = os.path.join(current_path, filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(source_code)
        
        print(f"Created script: {filepath}")
    
    def create_model_file(self, item_element, current_path, name, class_name):
        properties = self.extract_properties(item_element)
        
        extension = self.get_model_extension(class_name)
        filename = f"{name}{extension}"
        filepath = os.path.join(current_path, filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"-- {class_name} Properties\n")
            f.write(f"-- Name: {name}\n\n")
            
            for prop_name, prop_value in properties.items():
                if isinstance(prop_value, dict):
                    f.write(f"{prop_name} = {{\n")
                    for key, value in prop_value.items():
                        f.write(f"    {key} = {repr(value)},\n")
                    f.write("}\n\n")
                else:
                    f.write(f"{prop_name} = {repr(prop_value)}\n")
        
        print(f"Created model: {filepath}")
    
    def parse(self, rbxlx_file_path, output_directory):
        self.output_dir = output_directory
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        try:
            tree = ET.parse(rbxlx_file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            return False
        except FileNotFoundError:
            print(f"File not found: {rbxlx_file_path}")
            return False
        
        items = root.findall('Item')
        
        for item in items:
            self.process_item(item)
        
        print(f"Parsing complete. Output saved to: {self.output_dir}")
        return True

def main():
    if len(sys.argv) != 3:
        script_name = os.path.basename(sys.argv[0])
        print(f"Usage: python {script_name} <rbxlx_file> <output_folder>")
        print(f"Example: python {script_name} example.rbxlx Folder")
        sys.exit(1)
    
    rbxlx_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    parser = RBXLXParser()
    
    if parser.parse(rbxlx_file, output_dir):
        print("Successfully parsed RBXLX file!")
    else:
        print("Failed to parse RBXLX file.")
        sys.exit(1)

if __name__ == "__main__":
    main()
