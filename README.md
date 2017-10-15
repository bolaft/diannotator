# Overview

DiAnnotator is a dialogue annotation tool. It is meant to reduce the need to use the mouse to annotate dialogues and to improve keyboard-only annotation speed and reliability. DiAnnotator can be used to segment utterances, to apply dialogue act or sentiment-analysis labels, to link text segments and to modify taxonomies. DiAnnotator is fully multi-layer, and therefore supports annotation schemes such as DAMSL and ISO 24617-2.

# Requirements

#### Python version:

DiAnnotator is written in Python 3.4.3.

#### Python modules:

The following modules are required to run the program:

* `nltk`
* `ttkthemes`
* `undo`

# Run From Source

Simply run the Python script `launcher.py` in the `src` folder.

# Build Executable (optional)

Run the `build.sh` script at the root of the directory. A `bin` folder containing an executable will be created at the root of the project directory.

# Input Data Format

### CSV Format:

The file must contain a **header** line and as many additional lines as there are text segments. Columns must be separated by **tabs**, not commas, and there should be **no text delimiter**.

#### Columns:

The following columns are used when importing data:

##### `datetime`

Contains a string representation of the **date** and **time** on which the message was sent. The string must respect the international standard date and time notation to be parsed correctly.

##### `raw`

Contains the **raw text** of the message.

##### `segment`

Contains the **text segment**. When there are more than one segment in a message (due to prior segmentation for example), the `raw` column should only be filled in the first row, and left empty in the following rows. Moreover, when there are more than one raw message for a single segment (due to prior merging for example), the `segment` column should be filled only in the first row, and left empty in the following ones.

##### `participant`

Contains the **name** or **ID** of the speaker.

##### `note` (optional)

Contains a note or comment pertaining to the segment.

##### `<layer name>` (optional)

Columns bearing a layer name are used to load **legacy annotations**, which can serve as useful hints when producing new annotations. These column's names must follow the naming convention of the taxonomy's JSON file.

##### `<layer name>-value` (optional)

Columns bearing a layer name and suffixed by `-value` are used to load **legacy qualifiers** for that layer. For example, if `emotion` is a layer, `express` may be a label, and `happiness` might be the value present in the `emotion-value` column. These column's names must follow the naming convention of the taxonomy's JSON file.

##### `id` (optional)

Contains a unique identifier for the segment. This column is optional but is required for link importation.

##### `links` (optional)

Contains the list of links emanating from this segment, their types and their targets. The link format is the following: `<target_id>-<link_type>,<target_id>-<link_type>`. 

#### Example:

| participant   | datetime      | segment                                                               | raw                                                                   | activity  | social    | feedback      | feedback-value    |
|-------------  |-------    |--------------------------------------------------------------------   |--------------------------------------------------------------------   |---------- |--------   |-------------  |----------------   |
| manu          | 11-05-17 13:05    | hi guys!                                                  | hi guys! does anyone know how to install a proprietary graphics card driver?  |           | greet     |               |                   |
| manu          | 11-05-17 13:05    | does anyone know how to install a proprietary graphics card driver?                           |                                                                       | question  |           |               |                   |
| gabi          | 11-05-17 13:06    | search software sources, and then it's in the additional drivers tab | search software sources, and then it's in the additional drivers tab   | answer    |           |               |                   |
| manu          | 11-05-17 13:07    | k thx!                                                                | k thx!                                                                |           | thanks    | acknowledge   | positive          |

### JSON Format:

The file must contain an ordered list of dictionaries, each dictionary representing a single segment.

#### Fields:

Most fields are the same as for CSV data, with a few exceptions.

##### Annotations

The segment dictionary must not contain fields for each layer, instead there must be a field `annotations` that contains a dictionary. Each key of that dictionary is a layer and each value is another dictionary, with a `label` field containing the label of the segment for the layer and optionally a `qualifier` field containing the qualifier for the layer.

##### Links

Links must be represented as a dictionary in the optional `links` field of the segment dictionary. Each key of that dictionary represents a link type, and the corresponding value must be the list of identifiers of the target segments. The `id` field must be set for all segments for links to be imported correctly.

#### Example:

```json
{
    "id": 76,
    "segment": "Hello Gix,",
    "raw": "Hello Gix, how are you doing?",
    "participant": "Poggy",
    "datetime": "04-11-17 22:17",
    "note": "performed split here",
    "links": {
        "rhetorical relation": [
            75
        ]
    },
    "annotations": {
        "social obligations management": {
            "label": "greet"
        }
    }
}
```

# Taxonomy Format

When a data file is loaded, a taxonomy must be chosen before annotation can begin. Taxonomies are saved in JSON format.

#### Fields:

The taxonomy fields are:

##### `name`

The taxonomy's **name**.

##### `url` (optional)

The URL to the taxonomy's **website** or **documentation**.

##### `default`

The **default layer** of the taxonomy, the first one to be active when first loading a data file.

##### `labels`

A dictionary of lists, whose keys represent layer names and the lists' elements represent the layers' **labels' tagsets**.

##### `qualifiers`

A dictionary of lists, whose keys represent layer names and the lists' elements represent the layers' **qualifiers' tagsets**.

##### `links`

A dictionary whose keys represent the different **link types** and whose values represent the colors in which the links should be displayed.

##### `colors`

A dictionary, whose keys represent layer names and whose elements are **hexadecimal color codes** used for displaying labels. The `colors` field is mandatory but the dictionary may be left empty, in which case labels will be displayed in a randomly generated color.

#### Example:

```json
{
    "name": "J-22 Tax",
    "url": "www.somewhere-university.edu/j22tax",
    "default": "Task",
    "labels": {
        "Task": [
            "Inform",
            "Confirm",
            "Disconfirm",
            "Commit",
            "Offer",
            "Instruct",
            "Suggest",
            "Request Information",
            "Request Directives"
        ],
        "Communication": [
            "Correct",
            "Completion",
        ],
        "Other": [
            "Announce",
            "Preclose",
            "Switch Topic",
        ],
    },
    "qualifiers": {
        "Communication": [
            "Perception",
            "Interpretation",
            "Evaluation"
        ]
    },
    "links": {
        "Feedback": "#A6E22E",
        "Functional": "#54D6EF",
        "Rhetoric": "#ffffff"
    },
    "colors": {
        "Task": "#FFFFFF",
        "Communication": "#DB5CD7",
        "Other": "#DB5CD7"
    }
}
```

# Usage

### Annotation:

Black buttons on the bottom of the screen show the possible labels for the active layer. The active segment is the last one displayed, appearing in bold. To apply a label to a segment, click on the appropriate button or type a sufficiently discriminating part of the label (for example, `req dir` for `request directives`) then press Enter.

### Special Commands:

#### Change Layer: `Control C`

Changes the active layer.

#### Erase Annotation: `Control E`

Removes label and qualifier from the active segment.

#### Link Segment: `Control L`

If the active segment is not linked to any other segment, links it to a specific segment, selected by index after selecting the link type. If the segment is already linked to another segment of the selected link type, the link is removed.

#### Unlink Segment: `Control U`

Removes all links emanating from the active segment.

#### Split Segment: `Control S`

Splits the active segment in two, on the chosen token. Links, notes, annotations and legacy annotations are preserved.

#### Merge Segment: `Control M`

Merges the active segment to the previous ones. Links, notes, annotations and legacy annotations are preserved.

#### Add Element: `Control A`

Adds a new layer, label, qualifier or link type.

#### Rename Element: `Control R`

Updates the name of the layer, label, qualifier or link type used for the active segment. All segments annotated with this layer, label, qualifier or link type will be affected.

#### Jump To Segment: `Control J`

Jumps to a specific segment, selected by index.
 
#### Filter Collection: `Control F`

Filters the collection by label, legacy label, layer, legacy layer, qualifier or legacy qualifier.

#### Add Note: `Control N`

The next entry creates a note and attaches it to the active segment. If the active segment already has a note attached, the note is deleted.

### Keyboard Shortcuts:

#### `Enter`

Sends an entry, pushes a button on which the focus is set, or moves on to the next segment if the entry field is empty.

#### `Down Arrow`

Moves down one segment.

#### `Up Arrow`

Moves up one segment.

#### `Page Down`

Moves down ten segments.

#### `Page Up`

Moves up ten segments.

#### `Delete`

Deletes the active segment.

#### `F3`

Toggles legacy annotations display. 

#### `F4`

Randomizes participant colors.

#### `F5`

Filters segments by active layer.

#### `F6`

Filters segments by active label.

#### `F7`

Filters segments by active qualifier.

#### `F11`

Toggles between fullscreen and windowed mode.

#### `Escape`

Exits the application.

#### `Control +`

Increases text font size.

#### `Control -`

Decreases text font size.

#### `Tab`

Moves focus from button to button, and back to the entry field.

#### `Control W`

Closes the current file.

#### `Control O`

Opens the "open file" dialogue.

#### `Control Shift S`

Opens the "save as..." dialogue.

#### `Control Shift I`

Opens the "import file" dialogue.

#### `Control Shift E`

Opens the "export as..." dialogue.

#### `Control Alt I`

Opens the "import taxonomy" dialogue.

#### `Control Alt E`

Opens the "export taxonomy as..." dialogue.
