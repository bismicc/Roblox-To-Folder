import xml.etree.ElementTree as ET
import os
import base64
import re
import sys
import json
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
        if not protected_string:
            return ""
        try:
            # handle cdata wrapper
            if protected_string.startswith('<![CDATA[') and protected_string.endswith(']]>'):
                return protected_string[9:-3]
            # handle direct text content
            return protected_string
        except:
            return protected_string or ""
    
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
    
    def process_item(self, item_element, current_path="game", element_id_map=None):
        if element_id_map is None:
            element_id_map = {}
            
        class_name = item_element.get('class', 'Unknown')
        referent = item_element.get('referent', '')
        
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
        
        # create a unique id
        element_id = f"{current_path}/{sanitized_name}#{class_name}"
        
        if class_name in self.script_types:
            script_path = self.create_script_file(item_element, current_path, sanitized_name, class_name)
            
            element_id_map[script_path] = {
                'referent': referent,
                'element_id': element_id,
                'original_source': self.get_original_source(item_element)
            }
        else:
            model_path = self.create_model_file(item_element, current_path, sanitized_name, class_name)
            element_id_map[model_path] = {
                'referent': referent,
                'element_id': element_id,
                'original_props': self._extract_raw_properties(item_element)
            }
            
            children = item_element.findall('Item')
            if children:
                os.makedirs(item_path, exist_ok=True)
                
                for child in children:
                    element_id_map.update(self.process_item(child, item_path, element_id_map))
        
        return element_id_map
    
    def get_original_source(self, item_element):
        """Get the original source code from XML element"""
        props_element = item_element.find('Properties')
        if props_element is not None:
            source_element = props_element.find('.//ProtectedString[@name="Source"]')
            if source_element is not None and source_element.text:
                return self.decode_protected_string(source_element.text)
        return ""
    
    def create_script_file(self, item_element, current_path, name, class_name):
        source_code = self.get_original_source(item_element)
        
        extension = self.get_script_extension(class_name)
        filename = f"{name}{extension}"
        filepath = os.path.join(current_path, filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(source_code)
        
        print(f"Created script: {filepath}")
        return filepath
    
    def create_model_file(self, item_element, current_path, name, class_name):
        properties = self.extract_properties(item_element)
        
        extension = self.get_model_extension(class_name)
        filename = f"{name}{extension}"
        filepath = os.path.join(current_path, filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # store the original
        original_props = self._extract_raw_properties(item_element)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # metadata storing for rebuilding
            f.write(f"-- RBXLX_CLASS: {class_name}\n")
            f.write(f"-- RBXLX_NAME: {name}\n")
            f.write(f"-- RBXLX_ORIGINAL_PROPS: {repr(original_props)}\n")
            f.write(f"-- {class_name} Properties\n")
            f.write(f"-- Name: {name}\n")
            f.write(f"-- Edit the values below. Maintain the exact format for proper rebuilding.\n\n")
            
            for prop_name, prop_value in properties.items():
                if isinstance(prop_value, dict):
                    f.write(f"{prop_name} = {{\n")
                    for key, value in prop_value.items():
                        f.write(f"    {key} = {repr(value)},\n")
                    f.write("}\n\n")
                else:
                    f.write(f"{prop_name} = {repr(prop_value)}\n")
        
        print(f"Created model: {filepath}")
        return filepath
    
    def _extract_raw_properties(self, item_element):
        """Extract raw XML property data for perfect reconstruction"""
        raw_props = {}
        props_element = item_element.find('Properties')
        
        if props_element is not None:
            for prop in props_element:
                prop_name = prop.get('name', 'unknown')
                prop_info = {
                    'type': prop.tag,
                    'attributes': dict(prop.attrib),
                    'text': prop.text,
                    'children': []
                }
                
                # Store child elements for complex stuff
                for child in prop:
                    child_info = {
                        'tag': child.tag,
                        'text': child.text,
                        'attributes': dict(child.attrib)
                    }
                    prop_info['children'].append(child_info)
                
                raw_props[prop_name] = prop_info
        
        return raw_props
    
    def parse(self, rbxlx_file_path, output_directory):
        self.output_dir = output_directory
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        try:
            with open(rbxlx_file_path, 'r', encoding='utf-8') as f:
                original_xml_content = f.read()
            
            tree = ET.parse(rbxlx_file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            return False
        except FileNotFoundError:
            print(f"File not found: {rbxlx_file_path}")
            return False
        
        # save original
        original_xml_path = os.path.join(self.output_dir, ".original.rbxlx")
        with open(original_xml_path, 'w', encoding='utf-8') as f:
            f.write(original_xml_content)
        
        items = root.findall('Item')
        element_id_map = {}
        
        for item in items:
            element_id_map.update(self.process_item(item, element_id_map=element_id_map))
        
        # save element mapping
        mapping_path = os.path.join(self.output_dir, ".element_map.json")
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(element_id_map, f, indent=2)
        
        print(f"Parsing complete. Output saved to: {self.output_dir}")
        return True

    def rebuild_rbxlx(self, source_directory, output_rbxlx_path):
        """
        Rebuild RBXLX file using diff-based approach
        """
        original_xml_path = os.path.join(source_directory, ".original.rbxlx")
        mapping_path = os.path.join(source_directory, ".element_map.json")
        
        if not os.path.exists(original_xml_path):
            print("Error: Original RBXLX file not found. Cannot rebuild without template.")
            return False
        
        if not os.path.exists(mapping_path):
            print("Error: Element mapping not found. Cannot rebuild without mapping.")
            return False
        
        try:
            # read original xml
            with open(original_xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # load element mapping
            with open(mapping_path, 'r', encoding='utf-8') as f:
                element_map = json.load(f)
            
            # apply difference
            xml_content = self._apply_script_changes(xml_content, element_map, source_directory)
            
            # write the rbxlx
            with open(output_rbxlx_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            print(f"Rebuilt RBXLX file: {output_rbxlx_path}")
            return True
            
        except Exception as e:
            print(f"Error rebuilding RBXLX: {e}")
            return False
    
    def _apply_script_changes(self, xml_content, element_map, source_directory):
        """
        Apply changes to both script sources and model properties using text replacement on the raw XML
        """
        for file_path, element_info in element_map.items():
            if not os.path.exists(file_path):
                continue
            
            # handle scripts
            if file_path.endswith(('.server.lua', '.local.lua', '.module.lua', '.lua')):
                xml_content = self._apply_script_change(xml_content, file_path, element_info)
            
            # handle model files
            elif file_path.endswith('.model'):
                xml_content = self._apply_model_change(xml_content, file_path, element_info)
        
        return xml_content
    
    def _apply_script_change(self, xml_content, file_path, element_info):
        """Apply script source changes"""
        # read file
        with open(file_path, 'r', encoding='utf-8') as f:
            current_source = f.read()
        
        original_source = element_info.get('original_source', '')
        referent = element_info.get('referent', '')
        
        # only process if different
        if current_source != original_source:
            xml_content = self._replace_script_source(xml_content, referent, current_source)
        
        return xml_content
    
    def _apply_model_change(self, xml_content, file_path, element_info):
        """Apply model property changes"""
        try:
            # parse current model file
            current_props = self._parse_model_file(file_path)
            original_props_data = element_info.get('original_props', {})
            referent = element_info.get('referent', '')
            
            if not current_props or not referent:
                return xml_content
            
        
            original_props = self._raw_props_to_comparison(original_props_data)
            
            # check if the properties actually changed
            if current_props != original_props:
                xml_content = self._replace_model_properties(xml_content, referent, current_props, original_props_data)
            
        except Exception as e:
            print(f"Warning: Could not process model file {file_path}: {e}")
        
        return xml_content
    
    def _replace_script_source(self, xml_content, referent, new_source):
        """
        Replace script source in XML using precise text matching
        """
        if not referent:
            return xml_content
        
        # find the item
        item_pattern = f'<Item class="(?:Script|LocalScript|ModuleScript)"[^>]*referent="{re.escape(referent)}"[^>]*>'
        item_match = re.search(item_pattern, xml_content)
        
        if not item_match:
            return xml_content
        
        # find the source property
        item_start = item_match.start()
        
        # find the end
        item_end_pattern = r'</Item>'
        remaining_content = xml_content[item_start:]
        
        # Count Item tags to find matching closing tag
        open_count = 1
        pos = item_match.end() - item_start
        
        while open_count > 0 and pos < len(remaining_content):
            next_open = remaining_content.find('<Item', pos)
            next_close = remaining_content.find('</Item>', pos)
            
            if next_close == -1:
                break
            
            if next_open != -1 and next_open < next_close:
                open_count += 1
                pos = next_open + 5
            else:
                open_count -= 1
                if open_count == 0:
                    item_end = item_start + next_close + 7
                    break
                pos = next_close + 7
        else:
            # fallback
            return xml_content
        
        item_content = xml_content[item_start:item_end]
        
        # find and replace
        source_pattern = r'(<ProtectedString name="Source">)(.*?)(</ProtectedString>)'
        
        def replace_source(match):
            if new_source.strip():
                
                escaped_source = new_source.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Check if we need CDATA
                if any(char in new_source for char in ['&', '<', '>', '"', "'"]) or '\n' in new_source:
                    return f"{match.group(1)}<![CDATA[{new_source}]]>{match.group(3)}"
                else:
                    return f"{match.group(1)}{escaped_source}{match.group(3)}"
            else:
                return f"{match.group(1)}{match.group(3)}"
        
        new_item_content = re.sub(source_pattern, replace_source, item_content, flags=re.DOTALL)
        
    def _parse_model_file(self, file_path):
        """Parse a model file to extract current property values"""
        properties = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        current_dict = None
        current_dict_name = None
        
        for line in lines:
            line = line.strip()
            
           
            if line.startswith('--') or not line:
                continue
            
            
            if ' = {' in line and not line.endswith('}'):
                current_dict_name = line.split(' = {')[0].strip()
                current_dict = {}
            
            
            elif line == '}' and current_dict is not None:
                properties[current_dict_name] = current_dict
                current_dict = None
                current_dict_name = None
            
            
            elif current_dict is not None and ' = ' in line:
                key, value = line.split(' = ', 1)
                key = key.strip()
                value = value.rstrip(',').strip()
                try:
                    current_dict[key] = eval(value)
                except:
                    current_dict[key] = value.strip("'\"")
            
            
            elif ' = ' in line and current_dict is None:
                key, value = line.split(' = ', 1)
                key = key.strip()
                value = value.strip()
                try:
                    properties[key] = eval(value)
                except:
                    properties[key] = value.strip("'\"")
        
        return properties
    
    def _raw_props_to_comparison(self, raw_props):
        """Convert raw XML properties to comparison format"""
        comparison_props = {}
        
        for prop_name, prop_info in raw_props.items():
            prop_type = prop_info['type']
            
            if prop_type == 'string':
                comparison_props[prop_name] = prop_info['text'] or ""
            elif prop_type == 'bool':
                comparison_props[prop_name] = prop_info['text'] == 'true'
            elif prop_type in ['int', 'int64']:
                try:
                    comparison_props[prop_name] = int(prop_info['text'] or 0)
                except:
                    comparison_props[prop_name] = 0
            elif prop_type == 'float':
                try:
                    comparison_props[prop_name] = float(prop_info['text'] or 0)
                except:
                    comparison_props[prop_name] = 0.0
            elif prop_type == 'Vector3':
                vec_data = {}
                for child in prop_info['children']:
                    if child['tag'] in ['X', 'Y', 'Z']:
                        try:
                            vec_data[child['tag']] = float(child['text'] or 0)
                        except:
                            vec_data[child['tag']] = 0.0
                comparison_props[prop_name] = vec_data
            elif prop_type == 'Color3':
                color_data = {}
                for child in prop_info['children']:
                    if child['tag'] in ['R', 'G', 'B']:
                        try:
                            color_data[child['tag']] = float(child['text'] or 0)
                        except:
                            color_data[child['tag']] = 0.0
                comparison_props[prop_name] = color_data
            elif prop_type == 'UDim2':
                udim_data = {}
                for child in prop_info['children']:
                    if child['tag'] in ['XS', 'XO', 'YS', 'YO']:
                        try:
                            udim_data[child['tag']] = float(child['text'] or 0)
                        except:
                            udim_data[child['tag']] = 0.0
                comparison_props[prop_name] = udim_data
            elif prop_type == 'CoordinateFrame':
                cf_data = {'Position': {}, 'R00': 1, 'R01': 0}
                for child in prop_info['children']:
                    if child['tag'] in ['X', 'Y', 'Z']:
                        try:
                            cf_data['Position'][child['tag']] = float(child['text'] or 0)
                        except:
                            cf_data['Position'][child['tag']] = 0.0
                    elif child['tag'] in ['R00', 'R01']:
                        try:
                            cf_data[child['tag']] = float(child['text'] or (1 if child['tag'] == 'R00' else 0))
                        except:
                            cf_data[child['tag']] = 1 if child['tag'] == 'R00' else 0
                comparison_props[prop_name] = cf_data
            else:
                comparison_props[prop_name] = prop_info['text'] or ""
        
        return comparison_props
    
    def _replace_model_properties(self, xml_content, referent, new_props, original_raw_props):
        """Replace model properties in XML using precise text matching"""
        if not referent:
            return xml_content
        
        # find item with the referrant
        item_pattern = f'<Item class="[^"]*"[^>]*referent="{re.escape(referent)}"[^>]*>'
        item_match = re.search(item_pattern, xml_content)
        
        if not item_match:
            return xml_content
        
        # find the propertyu item in this element
        props_start_pattern = r'<Properties>'
        props_end_pattern = r'</Properties>'
        
        item_start = item_match.start()
        remaining_content = xml_content[item_start:]
        
        props_start_match = re.search(props_start_pattern, remaining_content)
        if not props_start_match:
            return xml_content
        
        props_start = item_start + props_start_match.end()
        props_end_match = re.search(props_end_pattern, xml_content[props_start:])
        if not props_end_match:
            return xml_content
        
        props_end = props_start + props_end_match.start()
        
        # gen new properties xml
        new_props_xml = self._generate_properties_xml(new_props, original_raw_props)
        
        return xml_content[:props_start] + new_props_xml + xml_content[props_end:]
    
    def _generate_properties_xml(self, new_props, original_raw_props):
        """Generate XML for properties, maintaining original structure where possible"""
        xml_parts = []
        
        for prop_name, prop_value in new_props.items():
            original_prop = original_raw_props.get(prop_name, {})
            prop_type = original_prop.get('type', 'string')
            
            # gen xml based on property type
            if prop_type == 'string':
                xml_parts.append(f'\n\t\t\t<string name="{prop_name}">{self._escape_xml(str(prop_value))}</string>')
            
            elif prop_type == 'bool':
                bool_val = 'true' if prop_value else 'false'
                xml_parts.append(f'\n\t\t\t<bool name="{prop_name}">{bool_val}</bool>')
            
            elif prop_type in ['int', 'int64']:
                xml_parts.append(f'\n\t\t\t<{prop_type} name="{prop_name}">{int(prop_value)}</{prop_type}>')
            
            elif prop_type == 'float':
                xml_parts.append(f'\n\t\t\t<float name="{prop_name}">{float(prop_value)}</float>')
            
            elif prop_type == 'Vector3' and isinstance(prop_value, dict):
                x = prop_value.get('X', 0)
                y = prop_value.get('Y', 0)
                z = prop_value.get('Z', 0)
                xml_parts.append(f'\n\t\t\t<Vector3 name="{prop_name}">')
                xml_parts.append(f'\n\t\t\t\t<X>{float(x)}</X>')
                xml_parts.append(f'\n\t\t\t\t<Y>{float(y)}</Y>')
                xml_parts.append(f'\n\t\t\t\t<Z>{float(z)}</Z>')
                xml_parts.append(f'\n\t\t\t</Vector3>')
            
            elif prop_type == 'Color3' and isinstance(prop_value, dict):
                r = prop_value.get('R', 0)
                g = prop_value.get('G', 0)
                b = prop_value.get('B', 0)
                xml_parts.append(f'\n\t\t\t<Color3 name="{prop_name}">')
                xml_parts.append(f'\n\t\t\t\t<R>{float(r)}</R>')
                xml_parts.append(f'\n\t\t\t\t<G>{float(g)}</G>')
                xml_parts.append(f'\n\t\t\t\t<B>{float(b)}</B>')
                xml_parts.append(f'\n\t\t\t</Color3>')
            
            elif prop_type == 'UDim2' and isinstance(prop_value, dict):
                xs = prop_value.get('XS', 0)
                xo = prop_value.get('XO', 0)
                ys = prop_value.get('YS', 0)
                yo = prop_value.get('YO', 0)
                xml_parts.append(f'\n\t\t\t<UDim2 name="{prop_name}">')
                xml_parts.append(f'\n\t\t\t\t<XS>{float(xs)}</XS>')
                xml_parts.append(f'\n\t\t\t\t<XO>{float(xo)}</XO>')
                xml_parts.append(f'\n\t\t\t\t<YS>{float(ys)}</YS>')
                xml_parts.append(f'\n\t\t\t\t<YO>{float(yo)}</YO>')
                xml_parts.append(f'\n\t\t\t</UDim2>')
            
            elif prop_type == 'CoordinateFrame' and isinstance(prop_value, dict):
                pos = prop_value.get('Position', {})
                x = pos.get('X', 0) if isinstance(pos, dict) else 0
                y = pos.get('Y', 0) if isinstance(pos, dict) else 0
                z = pos.get('Z', 0) if isinstance(pos, dict) else 0
                r00 = prop_value.get('R00', 1)
                r01 = prop_value.get('R01', 0)
                
                xml_parts.append(f'\n\t\t\t<CoordinateFrame name="{prop_name}">')
                xml_parts.append(f'\n\t\t\t\t<X>{float(x)}</X>')
                xml_parts.append(f'\n\t\t\t\t<Y>{float(y)}</Y>')
                xml_parts.append(f'\n\t\t\t\t<Z>{float(z)}</Z>')
                xml_parts.append(f'\n\t\t\t\t<R00>{float(r00)}</R00>')
                xml_parts.append(f'\n\t\t\t\t<R01>{float(r01)}</R01>')
                
                
                original_children = original_prop.get('children', [])
                rotation_elements = ['R02', 'R10', 'R11', 'R12', 'R20', 'R21', 'R22']
                for elem in rotation_elements:
                    value = 0
                    for child in original_children:
                        if child['tag'] == elem:
                            try:
                                value = float(child['text'] or 0)
                            except:
                                value = 0
                            break
                    xml_parts.append(f'\n\t\t\t\t<{elem}>{value}</{elem}>')
                
                xml_parts.append(f'\n\t\t\t</CoordinateFrame>')
            
            else:
                
                if original_prop:
                    
                    original_attrs = original_prop.get('attributes', {})
                    attr_str = ' '.join(f'{k}="{v}"' for k, v in original_attrs.items())
                    if original_prop.get('children'):
                        
                        xml_parts.append(f'\n\t\t\t<{prop_type} {attr_str}>')
                        for child in original_prop['children']:
                            child_attrs = ' '.join(f'{k}="{v}"' for k, v in child.get('attributes', {}).items())
                            xml_parts.append(f'\n\t\t\t\t<{child["tag"]} {child_attrs}>{child.get("text", "")}</{child["tag"]}>')
                        xml_parts.append(f'\n\t\t\t</{prop_type}>')
                    else:
                        
                        xml_parts.append(f'\n\t\t\t<{prop_type} {attr_str}>{self._escape_xml(str(prop_value))}</{prop_type}>')
                else:
                    # Fallback for unknown properties
                    xml_parts.append(f'\n\t\t\t<string name="{prop_name}">{self._escape_xml(str(prop_value))}</string>')
        
        return ''.join(xml_parts) + '\n\t\t'
    
    def _escape_xml(self, text):
        """Escape XML special characters"""
        if not isinstance(text, str):
            text = str(text)
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')

def main():
    if len(sys.argv) < 4:
        script_name = os.path.basename(sys.argv[0])
        print(f"Usage: python {script_name} <command> <input> <output>")
        print(f"Commands:")
        print(f"  parse <rbxlx_file> <output_folder>  - Parse RBXLX to folder structure")
        print(f"  rebuild <input_folder> <output_rbxlx> - Rebuild RBXLX from folder structure")
        print(f"Example: python {script_name} parse example.rbxlx Folder")
        print(f"Example: python {script_name} rebuild Folder rebuilt.rbxlx")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    input_path = sys.argv[2]
    output_path = sys.argv[3]
    
    parser = RBXLXParser()
    
    if command == "parse":
        if parser.parse(input_path, output_path):
            print("Successfully parsed RBXLX file!")
        else:
            print("Failed to parse RBXLX file.")
            sys.exit(1)
    elif command == "rebuild":
        if parser.rebuild_rbxlx(input_path, output_path):
            print("Successfully rebuilt RBXLX file!")
        else:
            print("Failed to rebuild RBXLX file.")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        print("Use 'parse' or 'rebuild'")
        sys.exit(1)

if __name__ == "__main__":
    main()
