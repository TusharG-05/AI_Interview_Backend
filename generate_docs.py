import json

def generate_markdown(openapi_path, output_path):
    with open(openapi_path, "r") as f:
        schema = json.load(f)

    md = "# API Documentation\n\n"
    md += "This document details the REST APIs for the application, including endpoint paths, methods, request parameters, request bodies, and response structures along with their data types.\n\n"
    md += "---\n\n"

    paths = schema.get("paths", {})
    components = schema.get("components", {}).get("schemas", {})

    def resolve_ref(ref_str):
        if not ref_str:
            return None
        schema_name = ref_str.split("/")[-1]
        return components.get(schema_name, {})

    def format_type(schema_obj):
        if not schema_obj:
            return "any"
        
        if "$ref" in schema_obj:
            ref_schema = resolve_ref(schema_obj["$ref"])
            return format_type(ref_schema)
            
        if "anyOf" in schema_obj:
            types = [format_type(t) for t in schema_obj["anyOf"]]
            return " | ".join(t for t in types if t and t != "null")
            
        t = schema_obj.get("type", "any")
        
        if t == "array":
            items = schema_obj.get("items", {})
            return f"Array<{format_type(items)}>"
            
        if t == "object":
            if "properties" in schema_obj:
                props = []
                required = schema_obj.get("required", [])
                for k, v in schema_obj["properties"].items():
                    req_str = " (Required)" if k in required else " (Optional)"
                    props.append(f"<li><b>{k}</b>: <code>{format_type(v)}</code>{req_str}</li>")
                return "<ul>" + "".join(props) + "</ul>"
            elif "additionalProperties" in schema_obj:
                add_props = schema_obj['additionalProperties']
                if isinstance(add_props, dict):
                    return f"Dict&lt;string, {format_type(add_props)}&gt;"
                else:
                    return "Dict&lt;string, any&gt;"
            return "object"
            
        return t

    for path, methods in paths.items():
        for method, details in methods.items():
            md += f"## `{method.upper()} {path}`\n\n"
            if "summary" in details:
                md += f"**Summary**: {details['summary']}\n\n"
            if "description" in details:
                md += f"{details['description']}\n\n"
                
            # Request Parameters (Query / Path)
            parameters = details.get("parameters", [])
            if parameters:
                md += "### Parameters\n"
                md += "| Name | Located in | Required | Type | Description |\n"
                md += "| --- | --- | --- | --- | --- |\n"
                for p in parameters:
                    req = "Yes" if p.get("required") else "No"
                    p_type = format_type(p.get("schema", {}))
                    desc = p.get("description", "")
                    md += f"| `{p['name']}` | {p['in']} | {req} | `{p_type}` | {desc} |\n"
                md += "\n"

            # Request Body
            req_body = details.get("requestBody", {})
            if req_body:
                md += "### Request Body\n"
                content = req_body.get("content", {})
                if "application/json" in content:
                    schema_obj = content["application/json"].get("schema", {})
                    md += format_type(schema_obj) + "\n\n"
                elif "multipart/form-data" in content:
                    md += "Content-Type: `multipart/form-data`\n\n"
                    schema_obj = content["multipart/form-data"].get("schema", {})
                    md += format_type(schema_obj) + "\n\n"
                elif "application/x-www-form-urlencoded" in content:
                    md += "Content-Type: `application/x-www-form-urlencoded`\n\n"
                    schema_obj = content["application/x-www-form-urlencoded"].get("schema", {})
                    md += format_type(schema_obj) + "\n\n"

            # Responses
            responses = details.get("responses", {})
            if responses:
                md += "### Responses\n"
                for code, resp in responses.items():
                    md += f"#### Status Code: `{code}`\n"
                    desc = resp.get("description", "")
                    if desc:
                        md += f"**Description**: {desc}\n\n"
                        
                    content = resp.get("content", {})
                    if "application/json" in content:
                        schema_obj = content["application/json"].get("schema", {})
                        md += "**Response Schema**:\n"
                        md += format_type(schema_obj) + "\n\n"
                    
            md += "---\n\n"

    with open(output_path, "w") as f:
        f.write(md)
    print(f"Documentation written to {output_path}")

generate_markdown("openapi.json", "api_docs.md")
