from pptx import Presentation
from pptx.util import Pt, Inches, Cm
from pptx.dml.color import RGBColor

def create_professional_presentation(data, output_file="professional_presentation.pptx"):
    prs = Presentation()
    
    for slide_data in data.get("slides", []):
        slide_layout_index = slide_data.get("layout", 1)
        slide_layout = prs.slide_layouts[slide_layout_index]
        slide = prs.slides.add_slide(slide_layout)

        if "title" in slide_data:
            title_shape = slide.shapes.title
            title_shape.text = slide_data["title"]
            title_font = slide_data.get("title_font", {})
            title_shape.text_frame.paragraphs[0].font.size = Pt(title_font.get("size", 32))
            title_shape.text_frame.paragraphs[0].font.bold = title_font.get("bold", False)
            title_shape.text_frame.paragraphs[0].font.color.rgb = RGBColor(*title_font.get("color", [0, 0, 0]))

        if "content" in slide_data:
            content_shape = slide.placeholders[1] if len(slide.placeholders) > 1 else None
            if content_shape:
                content_shape.text = ""
                for paragraph in slide_data["content"]:
                    p = content_shape.text_frame.add_paragraph()
                    p.text = paragraph.get("text", "")
                    font = p.font
                    font.size = Pt(paragraph.get("font_size", 18))
                    font.bold = paragraph.get("bold", False)
                    font.color.rgb = RGBColor(*paragraph.get("color", [85, 85, 85]))

        for image_data in slide_data.get("images", []):
            try:
                slide.shapes.add_picture(
                    image_data["path"],
                    Inches(image_data.get("x", 1)),
                    Inches(image_data.get("y", 1)),
                    width=Inches(image_data.get("width", 2)),
                    height=Inches(image_data.get("height", 2))
                )
            except FileNotFoundError:
                print(f"Image file '{image_data['path']}' not found. Skipping image.")

        for table_data in slide_data.get("tables", []):
            rows, cols = len(table_data["data"]), len(table_data["data"][0])
            x, y, width, height = table_data.get("x", 1), table_data.get("y", 1), table_data.get("width", 4), table_data.get("height", 1)
            table = slide.shapes.add_table(rows, cols, Inches(x), Inches(y), Inches(width), Inches(height)).table
            
            for i, col_width in enumerate(table_data.get("col_widths", [])):
                table.columns[i].width = Inches(col_width)

            for i, row in enumerate(table_data["data"]):
                for j, cell_text in enumerate(row):
                    cell = table.cell(i, j)
                    cell.text = cell_text

        for shape_data in slide_data.get("shapes", []):
            shape_type = shape_data.get("type", "rectangle").lower()
            x, y, width, height = shape_data.get("x", 1), shape_data.get("y", 1), shape_data.get("width", 2), shape_data.get("height", 1)
            fill_color = shape_data.get("color", [255, 255, 255])

            if shape_type == "rectangle":
                shape = slide.shapes.add_shape(
                    shape_data.get("shape_id", 1),
                    Inches(x),
                    Inches(y),
                    Inches(width),
                    Inches(height)
                )
                shape.fill.solid()
                shape.fill.fore_color.rgb = RGBColor(*fill_color)

    prs.save(output_file)
    print(f"Presentation saved as '{output_file}'.")

presentation_data = {
    "slides": [
        {
            "title": "Welcome to the Presentation",
            "layout": 0,
            "title_font": {"size": 36, "bold": True, "color": [0, 102, 204]},
            "content": [
                {"text": "This presentation demonstrates advanced features.", "font_size": 18, "bold": False, "color": [0, 0, 0]},
                {"text": "You can include images, tables, and shapes.", "font_size": 18, "bold": False, "color": [0, 0, 0]}
            ],
            "images": [
                {"path": "path/to/image.jpg", "x": 5, "y": 1, "width": 2, "height": 2}
            ]
        },
        {
            "title": "Data Table Example",
            "layout": 1,
            "tables": [
                {
                    "x": 1,
                    "y": 2,
                    "width": 6,
                    "height": 2,
                    "col_widths": [2, 2, 2],
                    "data": [
                        ["Name", "Age", "City"],
                        ["Alice", "25", "New York"],
                        ["Bob", "30", "San Francisco"]
                    ]
                }
            ]
        },
        {
            "title": "Shapes Example",
            "layout": 1,
            "shapes": [
                {"type": "rectangle", "x": 1, "y": 1, "width": 2, "height": 1, "color": [0, 255, 0]},
                {"type": "rectangle", "x": 4, "y": 1, "width": 2, "height": 1, "color": [255, 0, 0]}
            ]
        }
    ]
}

create_professional_presentation(presentation_data)
