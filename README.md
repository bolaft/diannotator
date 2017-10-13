# Overview

DiAnnotator is a dialogue annotation tool. It is meant to reduce the need to use the mouse to annotate dialogues and to improve keyboard-only annotation speed and reliability. DiAnnotator can be used to segment utterances, to apply dialogue act or sentiment-analysis labels, to link dialogue segments and to modify taxonomies. DiAnnotator is fully multi-layeral, and therefore supports annotation schemes such as DAMSL and ISO 24617-2.

# Requirements

#### Python version:

DiAnnotator is written in Python 3.4.3.

#### Python modules:

The following modules are required to run the program:

* `nltk`
* `ttkthemes`

# Run From Source

Simply run the Python script `launcher.py` in the `src` folder.

# Build Executable (optional)

Run the build.sh script at the root of the directory. A `bin` folder containing an executable will be created at the root of the project directory.

# Input Data Format

### Location:

Raw data files should be placed in the `csv` folder at the root of the project directory.

### Format:

The only accepted format is **CSV**. The file must contain a **header** line and as many additional lines as there are dialogue segments. Columns must be separated by **tabs**, not commas, and there should be **no text delimiter**.

#### Columns:

The following columns are used when importing data:

##### `time`

Contains a string representation of the **time** at which the message was sent.

##### `date`

Contains a string representation of the **date** on which the message was sent.

##### `raw`

Contains the **raw text** of the message.

##### `segment`

Contains the **dialogue segment**. When there are more than one segment in a message (due to prior segmentation for example), the `raw` column should only be filled in the first row, and left empty in the following rows. Moreover, when there are more than one raw message for a single segment (due to prior merging for example), the `segment` column should be filled only in the first row, and left empty in the following ones.

##### `participant`

Contains the **name** or **ID** of the speaker.

##### `note` (optional)

Contains a note or comment pertaining to the segment.

##### `<layer name>` (optional)

Columns bearing a layer name are used to load **legacy annotations**, which can serve as useful hints when producing new annotations. These column's names must follow the naming convention of the taxonomy's JSON file.

##### `<layer name>-value` (optional)

Columns bearing a layer name and suffixed by `-value` are used to load **legacy qualifiers** for that layer. For example, if `emotion` is a layer, `express` may be a label, and `happiness` might be the value present in the `emotion-value` column. These column's names must follow the naming convention of the taxonomy's JSON file.

#### Example:

| participant 	| date     	| time  	| segment                                                            	| raw                                                                	| activity 	| social 	| feedback    	| feedback-value 	|
|-------------	|----------	|-------	|--------------------------------------------------------------------	|--------------------------------------------------------------------	|----------	|--------	|-------------	|----------------	|
| manu        	| 11-05-17 	| 13:05 	| hi guys!                                              	| hi guys! does anyone know how to install a proprietary graphics card driver? 	|          	| greet  	|             	|                	|
| manu        	| 11-05-17 	| 13:05 	| does anyone know how to install a proprietary graphics card driver?                       	|                                                                    	| question 	|        	|             	|                	|
| gabi        	| 11-05-17 	| 13:06 	| search software sources, and then it's in the additional drivers tab | search software sources, and then it's in the additional drivers tab 	| answer   	|        	|             	|                	|
| manu        	| 11-05-17 	| 13:07 	| k thx!                                                             	| k thx!                                                             	|          	| thanks 	| acknowledge 	| positive       	|

# Taxonomy Format

When a CSV file is loaded, a taxonomy must be chosen before annotation can begin. Taxonomies are saved in JSON format. Their fields are:

#### `name`

The taxonomy's **name**.

#### `url` (optional)

The URL to the taxonomy's **website** or **documentation**.

#### `default`

The **default layer** of the taxonomy, the first one to be active when first loading a data file.

#### `labels`

A dictionary of lists, whose keys represent layer names and the lists' elements represent the layers' **labels' tagsets**.

#### `qualifiers`

A dictionary of lists, whose keys represent layer names and the lists' elements represent the layers' **qualifiers' tagsets**.

#### `links`

A dictionary whose keys represent the different **link types** and whose values represent the colors in which the links should be displayed.

#### `colors`

A dictionary, whose keys represent layer names and whose elements are **hexadecimal color codes** used for displaying labels. The `colors` field is mandatory but the dictionary may be left empty, in which case labels will be displayed in a randomly generated color.

# Usage

### Annotation:

Black buttons on the bottom of the screen show the possible labels for the active layer. The active segment is the last one displayed, appearing in bold. To apply a label to a segment, click on the appropriate button or type a sufficiently discriminating part of the label (for example, `req dir` for `request directives`) then press Enter.

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

#### `Control J`

Jumps to a specific segment, selected by index.

#### `Delete`

Deletes the active segment.

#### `F3`

Randomizes participant colors.

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

#### `Control O`

Opens the "open data file" dialogue.

#### `Control Shift S`

Opens the "save as..." dialogue.

#### `Control Shift E`

Opens the "export as..." dialogue.

### Special Commands:

#### Change Layer : `Control C`

Changes the active layer.

#### Erase Annotation : `Control E`

Removes label and qualifier from the active segment.

#### Link Segment : `Control L`

If the active segment is not linked to any other segment, links it to a specific segment, selected by index after selecting the link type. If the segment is already linked to another segment of the selected link type, the link is removed.

### Unlink Segment : `Control U`

Removes all links emanating from the active segment.

#### Split Segment : `Control S`

Splits the active segment in two, on the chosen token. Links, notes, annotations and legacy annotations are preserved.

#### Merge Segment : `Control M`

Merges the active segment to the previous ones. Links, notes, annotations and legacy annotations are preserved.

#### Add Tag : `Control A`

The next entry creates a new label added to the active layer, or creates a new qualifier for the active layer, if applicable.

#### Rename Tag : `Control R`

Updates the name of the label or qualifier used for the active segment, on the active layer. All segments annotated with this label or qualifier will be affected.
 
#### Filter By Label : `Control F`

Displayed segments are filtered to only display those bearing the same annotation as the active segment for the active layer. If the segment doesn't have a label on the active layer, the filter is created to only display segments bearing the same legacy annotation for the active layer. Using this command again will remove the filter and display all segments.

#### Add Note : `Control N`

The next entry creates a note and attaches it to the active segment. If the active segment already has a note attached, the note is deleted.
