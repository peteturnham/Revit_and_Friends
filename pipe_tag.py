from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Plumbing import Pipe
import math

# Convert Revit internal units to feet
def to_feet(val_internal):
    return UnitUtils.ConvertFromInternalUnits(val_internal, UnitTypeId.Feet)

# Determine vertical length & direction
def get_vertical_info(pipe):
    curve = pipe.Location.Curve
    start = curve.GetEndPoint(0)
    end = curve.GetEndPoint(1)
    startZ = to_feet(start.Z)
    endZ = to_feet(end.Z)
    vertical_length = abs(endZ - startZ)

    if endZ > startZ:
        direction = "Up"
    elif endZ < startZ:
        direction = "Down"
    else:
        direction = "Horizontal"

    return vertical_length, direction

# Get pipe system abbreviation (e.g., CHWS, SAN)
def get_system_abbrev(doc, pipe):
    system_id = pipe.MEPSystem
    if system_id:
        system = doc.GetElement(system_id.Id)
        if system and system.LookupParameter("Abbreviation"):
            return system.LookupParameter("Abbreviation").AsString()
    return "UNK"  # fallback if no abbreviation

# Tag vertical risers/drops
def tag_risers(doc):
    up_count = 1
    down_count = 1
    min_height = 10.0  # ft

    view = doc.ActiveView
    collector = FilteredElementCollector(doc, view.Id).OfClass(Pipe)

    t = Transaction(doc, "Tag Vertical Pipes with System")
    t.Start()

    for pipe in collector:
        vertical_length, direction = get_vertical_info(pipe)

        if vertical_length >= min_height and direction in ["Up", "Down"]:
            # Get system abbreviation
            sys_abbrev = get_system_abbrev(doc, pipe)

            # Assign tag text
            if direction == "Up":
                tag_text = f"R{up_count}-{sys_abbrev}"
                up_count += 1
            else:
                tag_text = f"D{down_count}-{sys_abbrev}"
                down_count += 1

            # Create tag with offset
            midpoint = (pipe.Location.Curve.GetEndPoint(0) + pipe.Location.Curve.GetEndPoint(1)) / 2
            offset_point = XYZ(midpoint.X + 2, midpoint.Y + 2, midpoint.Z)

            tag = IndependentTag.Create(
                doc,
                doc.ActiveView.Id,
                Reference(pipe),
                False,
                TagMode.TM_ADDBY_CATEGORY,
                TagOrientation.Horizontal,
                offset_point,
            )

            tag.HasLeader = True
            tag.LeaderEndCondition = LeaderEndCondition.Free
            tag.TagText = tag_text

    t.Commit()
    TaskDialog.Show("Done", "Vertical risers/drops tagged with system abbreviation!")

# Run
tag_risers(__revit__.ActiveUIDocument.Document)
