
## Nighty UI/API Documentation

## Table of Contents
- [Nighty UI/API Documentation](#nighty-uiapi-documentation)
- [Table of Contents](#table-of-contents)
- [UI Scripting](#ui-scripting)
  - [Overview](#overview)
  - [Important: UI Scripts vs Command Scripts](#important-ui-scripts-vs-command-scripts)
  - [Getting Started with UI Scripting](#getting-started-with-ui-scripting)
  - [Basic Example](#basic-example)
  - [Component Hierarchy](#component-hierarchy)
  - [Creating Complex Layouts](#creating-complex-layouts)
  - [Working with Forms](#working-with-forms)
  - [Best Practices](#best-practices)
    - [Script-Specific Naming Conventions](#script-specific-naming-conventions)
      - [Example of Naming Collision (Problem):](#example-of-naming-collision-problem)
      - [Solution: Use Script-Specific Prefixes](#solution-use-script-specific-prefixes)
      - [Best Practices for Prefixes:](#best-practices-for-prefixes)
- [API Reference](#api-reference)
  - [Tab Component](#tab-component)
    - [Class `Tab`](#class-tab)
      - [Constructor](#constructor)
      - [Parameters](#parameters)
      - [Methods](#methods)
  - [CardContainer Component](#cardcontainer-component)
    - [Class `CardContainer`](#class-cardcontainer)
      - [Creator Method (`Tab.create_container` or `CardContainer.create_container`)](#creator-method-tabcreate_container-or-cardcontainercreate_container)
      - [Parameters (passed to `create_container`)](#parameters-passed-to-create_container)
      - [Methods](#methods-1)
  - [Card Component](#card-component)
    - [Class `Card`](#class-card)
      - [Creator Method (`CardContainer.create_card`)](#creator-method-cardcontainercreate_card)
      - [Parameters (passed to `create_card`)](#parameters-passed-to-create_card)
      - [Methods](#methods-2)
  - [Group Component](#group-component)
    - [Class `Group`](#class-group)
      - [Creator Method (`Card.create_group` or `Group.create_group`)](#creator-method-cardcreate_group-or-groupcreate_group)
      - [Parameters (passed to `create_group`)](#parameters-passed-to-create_group)
      - [Methods](#methods-3)
  - [UI Elements](#ui-elements)
    - [Shared Attributes \& Parameters](#shared-attributes--parameters)
    - [Text](#text)
      - [Parameters](#parameters-1)
      - [Attributes (Read/Write)](#attributes-readwrite)
    - [Button](#button)
      - [Parameters](#parameters-2)
      - [Attributes (Read/Write)](#attributes-readwrite-1)
    - [Input](#input)
      - [Parameters](#parameters-3)
      - [Attributes (Read/Write)](#attributes-readwrite-2)
    - [Image](#image)
      - [Parameters](#parameters-4)
      - [Attributes (Read/Write)](#attributes-readwrite-3)
    - [Select](#select)
      - [Parameters](#parameters-5)
      - [Attributes (Read/Write)](#attributes-readwrite-4)
    - [Dynamic UI Element Visibility](#dynamic-ui-element-visibility)
    - [Server and Channel Selection Example](#server-and-channel-selection-example)
    - [Server and Channel Filtering](#server-and-channel-filtering)


## UI Scripting

UI Scripting allows you to use the Nighty scripting engine to write Python scripts that dynamically create and update elements within Nighty's graphical user interface.

> **Note**: This guide primarily covers features available in Nighty 2.4 Beta and later. UI scripting is an evolving feature.

If you need to update Nighty, check the official Discord server: [Get Links](https://discord.gg/nighty).

### Overview

With UI Scripting, you can add custom tabs to the Nighty application. These tabs can contain various interactive elements like text displays, buttons, input fields, dropdowns, and images, all managed by your Python script. This allows for creating configuration interfaces, dashboards, or tools directly within Nighty.

### Important: UI Scripts vs Command Scripts

Understand the fundamental differences:

1.  **Integration**: UI scripts automatically appear as *tabs* in the Nighty interface. They are **not** triggered by Discord commands (e.g., `<p>myuiscript`).
2.  **Control**: Interaction happens *entirely within the Nighty UI tab* (clicking buttons, entering text). Discord commands do not control the UI script's elements.
3.  **Persistence**: UI tabs created by scripts remain visible and active as long as Nighty is running and the script is loaded.
4.  **Independence**: UI scripts operate separately from the Discord command processing system. They have their own event loops for handling UI interactions (like button clicks).

*Example*: A script creating a "Settings Manager" UI tab would present options within that tab in Nighty. Users would click buttons or type into fields *in Nighty*, not by typing commands in Discord.

### Getting Started with UI Scripting

The basic workflow involves:

1.  Importing `Tab` and `UI` (implicitly available, do not use `from nighty import ...`).
2.  Creating a `Tab` instance, giving it a unique name and optionally an icon.
3.  Creating one or more `CardContainer` instances within the tab to define the layout (columns or rows).
4.  Creating `Card` instances within containers to hold the actual UI elements.
5.  Creating UI elements (e.g., `UI.Text`, `UI.Button`, `UI.Input`) inside the cards or organizing them within `Group` elements.
6.  Assigning callback functions (event handlers) to interactive elements (like `button.onClick`).
7.  Calling the `tab.render()` method *last* to build and display the UI tab.

### Basic Example

```python
@nightyScript(
    name="Basic UI Example",
    author="Your Name",
    description="A simple UI tab with text and a button.",
    usage="Enable this script and check the Nighty UI tabs."
)
def basic_ui_script():
    """
    BASIC UI EXAMPLE
    ---------------
    Creates a simple tab in the Nighty UI with a title and a button
    that prints a message to the Nighty console when clicked.
    """
    try:
        # Create a new tab
        # Use script-specific prefix for the tab name if needed
        tab_name = "basic_ui_tab"
        my_tab = Tab(name=tab_name, icon="star", title="My First UI Tab") # Add a title

        # Create a container (defaults to columns)
        container = my_tab.create_container()

        # Create a card inside the container
        # Add some padding/gap and alignment
        card = container.create_card(gap=4, vertical_align="center", horizontal_align="center")

        # Add a text element to the card
        card.create_ui_element(UI.Text, content="Hello from NightyScript UI!", size="xl", color="accent")

        # Add a button
        # Use script-specific prefix for variable name
        basic_ui_click_button = card.create_ui_element(UI.Button, label="Click Me!", variant="cta")

        # --- Define the Button's Click Handler ---
        # Use script-specific prefix for function name
        def basic_ui_on_button_click():
            log_message = "Basic UI button was clicked!"
            print(log_message, type_="INFO") # Log to Nighty console
            # Optionally show a toast notification in the UI
            try:
                my_tab.toast(title="Button Clicked", description=log_message, type="SUCCESS")
            except Exception as e:
                print(f"Failed to show toast: {e}", type_="WARNING")

        # Assign the handler to the button's onClick event
        basic_ui_click_button.onClick = basic_ui_on_button_click

        # --- IMPORTANT: Render the tab ---
        # This must be called after all elements are defined.
        my_tab.render()

        print(f"Basic UI Example script loaded. Tab '{tab_name}' created.", type_="SUCCESS")

    except Exception as e:
        # Log any error during UI setup
        print(f"Error setting up Basic UI Example: {e}", type_="ERROR")
        # Include traceback if possible (using a logging helper is better)
        import traceback
        print(traceback.format_exc(), type_="ERROR")

# --- IMPORTANT: Call the main function to register the script ---
basic_ui_script()

```

### Component Hierarchy

The structure of a UI tab follows this hierarchy:

1.  **`Tab`**: The root component. Represents the tab itself in Nighty's sidebar. Contains `CardContainer`s.
2.  **`CardContainer`**: Organizes `Card`s. Can be type `"columns"` (side-by-side) or `"rows"` (stacked vertically). Can be nested. Contains `Card`s.
3.  **`Card`**: A visual block with a background, padding, and optional border. Contains `UI Elements` or `Group`s.
4.  **`Group`**: An invisible container used purely for layout. Organizes multiple `UI Elements` horizontally (`"columns"`) or vertically (`"rows"`). Can be nested. Contains `UI Elements` or other `Group`s.
5.  **`UI Elements`**: The visible components users interact with: `UI.Text`, `UI.Button`, `UI.Input`, `UI.Select`, `UI.Image`, etc.

```mermaid
graph TD
    Tab --> CardContainer1[CardContainer (type='rows')]
    Tab --> CardContainer2[CardContainer (type='columns')]

    CardContainer1 --> Card1[Card]
    CardContainer1 --> Card2[Card]

    CardContainer2 --> Card3[Card]
    CardContainer2 --> Card4[Card]

    Card1 --> Text1[UI.Text]
    Card1 --> Button1[UI.Button]

    Card2 --> Group1[Group (type='columns')]
    Group1 --> Input1[UI.Input]
    Group1 --> Button2[UI.Button]

    Card3 --> Image1[UI.Image]
    Card4 --> Select1[UI.Select]
```

### Creating Complex Layouts

Combine `CardContainer`s (rows/columns) and `Group`s to achieve sophisticated layouts.

```python
# (Inside a script function like basic_ui_script)
try:
    complex_tab = Tab(name="complex_layout_tab", icon="chart", title="Complex Layout Demo")

    # Main container: Rows layout (top section, bottom section)
    main_container = complex_tab.create_container(type="rows", gap=4) # Gap between top and bottom

    # --- Top Section: Two cards side-by-side ---
    top_container = main_container.create_container(type="columns", gap=4) # Gap between left and right cards
    left_card = top_container.create_card(title="Left Card") # Cards can have titles
    right_card = top_container.create_card(title="Right Card")

    # Content for left card
    left_card.create_ui_element(UI.Text, content="This is the left card content.", size="base")
    left_card.create_ui_element(UI.Button, label="Left Button", variant="bordered")

    # Content for right card using a Group for alignment
    right_group = right_card.create_group(type="rows", gap=2, vertical_align="center")
    right_group.create_ui_element(UI.Text, content="Right card items:", weight="bold") # Bold text
    right_group.create_ui_element(UI.Input, placeholder="Enter something...")
    right_group.create_ui_element(UI.Button, label="Right Button", variant="solid")

    # --- Bottom Section: One card spanning the width ---
    # No need for a container if it's just one card, add directly to main_container
    bottom_card = main_container.create_card(title="Bottom Card")
    bottom_card.create_ui_element(UI.Text, content="This card is below the two top cards.", size="lg")

    complex_tab.render()
    print("Complex Layout UI Example loaded.", type_="SUCCESS")

except Exception as e:
    print(f"Error setting up Complex Layout UI: {e}", type_="ERROR")
    import traceback
    print(traceback.format_exc(), type_="ERROR")

```

### Working with Forms

Create interactive forms by using `UI.Input`, `UI.Select`, etc., and handling submission or changes with event handlers.

```python
# (Inside a script function)
try:
    form_tab = Tab(name="form_tab", icon="inbox", title="Simple Form")
    form_container = form_tab.create_container()
    form_card = form_container.create_card(title="User Input Form", gap=4)

    form_card.create_ui_element(UI.Text, content="Please fill out the form:", size="lg")

    # --- Input Fields ---
    # Use script-specific names for element variables
    form_name_input = form_card.create_ui_element(UI.Input, label="Full Name", placeholder="Enter your full name")
    form_email_input = form_card.create_ui_element(UI.Input, label="Email Address", placeholder="you@example.com", type="email") # Input type validation
    form_message_input = form_card.create_ui_element(UI.Input, label="Your Message", placeholder="Type your message here", multiline=True, rows=4) # Multiline text area

    # --- Submit Button ---
    form_submit_button = form_card.create_ui_element(UI.Button, label="Submit Form", variant="cta")

    # --- Status Text (to show feedback) ---
    form_status_text = form_card.create_ui_element(UI.Text, content="", size="sm", color="secondary") # Initially empty

    # --- Submit Handler ---
    # Use script-specific name
    def form_on_submit():
        # Access input values using the .value attribute
        name = form_name_input.value
        email = form_email_input.value
        message = form_message_input.value

        # Basic validation
        if not name or not email or not message:
            form_status_text.content = "Error: Please fill out all fields."
            form_status_text.color = "error"
            form_tab.toast(title="Form Error", description="Please fill out all fields.", type="ERROR")
            return

        log_message = f"Form submitted:\nName: {name}\nEmail: {email}\nMessage: {message}"
        print(log_message, type_="INFO")

        # Provide feedback in the UI
        form_status_text.content = f"Success: Form submitted for {name}."
        form_status_text.color = "success"
        form_tab.toast(title="Form Submitted", description=f"Data for {name} received.", type="SUCCESS")

        # Optionally clear the form fields
        form_name_input.value = ""
        form_email_input.value = ""
        form_message_input.value = ""

    # Assign the handler
    form_submit_button.onClick = form_on_submit

    form_tab.render()
    print("Form UI Example loaded.", type_="SUCCESS")

except Exception as e:
    print(f"Error setting up Form UI: {e}", type_="ERROR")
    import traceback
    print(traceback.format_exc(), type_="ERROR")
```

### Best Practices

1.  **Organization**: Use `CardContainer`s and `Group`s logically to structure your UI. Avoid overly deep nesting.
2.  **Alignment & Spacing**: Utilize `horizontal_align`, `vertical_align`, and `gap` parameters in Cards, Containers, and Groups for consistent layout.
3.  **Interactivity**: Implement clear event handlers (`onClick`, `onChange`, `onInput`) for buttons, inputs, selects, etc. Provide feedback to the user (e.g., status text, toast notifications).
4.  **Error Handling**: Wrap UI setup code and event handlers in `try...except` blocks. Log errors using `print(..., type_="ERROR")` and potentially show user-friendly messages via `tab.toast`.
5.  **Naming Conventions**: **Crucially**, use script-specific prefixes for UI element variables and event handler function names to prevent conflicts between different UI scripts running simultaneously (see below).
6.  **Performance**: For complex UIs or those handling lots of data, be mindful of performance. Avoid heavy computations directly within event handlers; use `run_in_thread` if necessary for blocking tasks triggered by UI interaction.
7.  **Testing**: Test your UI thoroughly within Nighty.

#### Script-Specific Naming Conventions

When multiple UI scripts run concurrently, using generic names like `submit_button` or `on_change` can lead to conflicts where Nighty's UI framework might mistakenly connect an event from one script's element to another script's handler.

**Always prefix UI element variables and their corresponding event handler functions with a unique identifier related to your script.**

##### Example of Naming Collision (Problem):

```python
# --- In weather_ui_script.py ---
update_button = card.create_ui_element(UI.Button, label="Update Weather")
def on_update(): # Generic handler name
    # Fetch weather data...
update_button.onClick = on_update

# --- In stock_ui_script.py ---
update_button = card.create_ui_element(UI.Button, label="Update Stocks")
def on_update(): # Identical generic handler name!
    # Fetch stock data...
update_button.onClick = on_update
```
*Result:* Clicking the weather update button might incorrectly trigger the stock update logic, or vice-versa.

##### Solution: Use Script-Specific Prefixes

```python
# --- In weather_ui_script.py ---
WEATHER_SCRIPT_PREFIX = "weather_" # Define a prefix
weather_update_button = card.create_ui_element(UI.Button, label="Update Weather")
def weather_on_update(): # Prefixed handler name
    # Fetch weather data...
weather_update_button.onClick = weather_on_update

# --- In stock_ui_script.py ---
STOCK_SCRIPT_PREFIX = "stock_" # Define a different prefix
stock_update_button = card.create_ui_element(UI.Button, label="Update Stocks")
def stock_on_update(): # Prefixed handler name
    # Fetch stock data...
stock_update_button.onClick = stock_on_update
```
*Result:* Each button click now correctly calls its own script's specific handler function.

##### Best Practices for Prefixes:

1.  **Choose a Unique Prefix**: Use a short, descriptive prefix for your script (e.g., `translator_`, `logger_`, `greet_ui_`).
2.  **Apply Consistently**: Use the prefix for:
    *   Variables holding UI elements (`translator_language_select`).
    *   Event handler functions (`translator_on_language_change`).
    *   Helper functions primarily used by the UI (`translator_update_display`).
    *   Consider prefixing Tab names (`translator_tab`) too.
3.  **Document**: Mention the prefix convention in your script's internal comments if helpful.

This discipline prevents hard-to-debug issues caused by naming conflicts in the shared UI environment.

## API Reference

This reference details the components and elements available for UI scripting.

*(Work in progress - UI scripting is evolving)*

### Tab Component

The top-level container for your custom UI page, appearing as a clickable tab in Nighty's interface.

#### Class `Tab`

##### Constructor

```python
# Minimum required: unique name
my_tab = Tab(name="my_unique_tab_name")

# All parameters:
my_tab = Tab(
    name="my_unique_tab_name", # Required, max 36 chars, unique across all scripts
    icon="star",                # Optional: Icon name (e.g., 'users', 'star', 'chart', 'inbox', 'message', 'settings')
    gap=8,                      # Optional: Default spacing between CardContainers within this tab (default: 6)
    title="My Awesome UI Tab"   # Optional: Text displayed at the very top of the tab's content area
)
```

##### Parameters

| Parameter | Type     | Required | Default   | Description                                                                 |
| :-------- | :------- | :------- | :-------- | :-------------------------------------------------------------------------- |
| `name`    | `string` | Yes      |           | Unique identifier (max 36 chars). **Use script-specific prefixes!**         |
| `icon`    | `string` | No       | `None`    | Icon shown in the tab list (e.g., `users`, `star`, `chart`, `message`).     |
| `gap`     | `int`    | No       | `6`       | Default spacing between direct child `CardContainer` elements.              |
| `title`   | `string` | No       | `None`    | Text displayed prominently at the top of the tab's content area.            |

##### Methods

| Method                             | Returns       | Description                                                                                                                               |
| :--------------------------------- | :------------ | :---------------------------------------------------------------------------------------------------------------------------------------- |
| `create_container(type, **kwargs)` | `CardContainer` | Adds a new `CardContainer` to the tab. See [CardContainer Component](#cardcontainer-component).                                           |
| `render()`                         | `None`        | Finalizes and displays the tab in the UI. **Call this last.**                                                                             |
| `toast(title, description, type)`  | `None`        | Shows a temporary notification popup within the Nighty app.<br>**Parameters:**<br>- `title` (`string`): Required.<br>- `description` (`string`): Required.<br>- `type` (`string`): Required. `"INFO"`, `"ERROR"`, or `"SUCCESS"`. |

### CardContainer Component

Organizes `Card` elements within a `Tab` or another `CardContainer`. Controls the layout direction (columns or rows).

#### Class `CardContainer`

> **Important**: Do not instantiate directly. Use `tab.create_container()` or `parent_container.create_container()`.

At least one `CardContainer` is typically needed within a `Tab`. Nesting is allowed for complex layouts (e.g., rows within columns), but keep it manageable.

##### Creator Method (`Tab.create_container` or `CardContainer.create_container`)

```python
# Basic container (defaults to 'columns', height='full')
container = tab.create_container()

# Container with rows layout and custom gap
rows_container = tab.create_container(type="rows", gap=4)

# Nested container
parent_container = tab.create_container(type="columns", width="full")
# Child container taking auto width within the parent column
child_container = parent_container.create_container(type="rows", width="auto", gap=2)
```

##### Parameters (passed to `create_container`)

| Parameter          | Type                 | Default    | Description                                                                                                   |
| :----------------- | :------------------- | :--------- | :------------------------------------------------------------------------------------------------------------ |
| `type`             | `"columns"`, `"rows"`| `"columns"`| Layout direction for child `Card`s or nested `CardContainer`s.                                                |
| `width`            | `"auto"`, `"full"`   | `"full"`   | How much horizontal space the container tries to occupy. `"auto"` shrinks to content.                         |
| `height`           | `"auto"`, `"full"`   | `"full"`   | How much vertical space the container tries to occupy. `"auto"` shrinks to content. (Often less impactful than width). |
| `gap`              | `int`                | `6`        | Spacing *between* the direct children (Cards or nested Containers) within this container.                       |
| `vertical_align`   | `"top"`, `"center"`, `"bottom"` | `"top"` | How children are aligned vertically within this container (if container has extra space). |
| `horizontal_align` | `"left"`, `"center"`, `"right"`| `"left"` | How children are aligned horizontally within this container (if container has extra space). |

##### Methods

| Method                           | Returns     | Description                                                    |
| :------------------------------- | :---------- | :------------------------------------------------------------- |
| `create_card(**kwargs)`          | `Card`      | Adds a new `Card` to this container. See [Card Component](#card-component). |
| `create_container(**kwargs)`     | `CardContainer` | Adds a nested `CardContainer` to this container.                 |

### Card Component

A distinct visual block with a background, padding, and optional title, used to group related UI elements.

#### Class `Card`

> **Important**: Do not instantiate directly. Use `container.create_card()`.

##### Creator Method (`CardContainer.create_card`)

```python
# Basic card
simple_card = container.create_card()

# Card with title, gap, and centered content
styled_card = container.create_card(
    title="Settings",
    gap=4,
    vertical_align="center",
    horizontal_align="center"
)
```

##### Parameters (passed to `create_card`)

| Parameter          | Type                 | Default    | Description                                                                                                   |
| :----------------- | :------------------- | :--------- | :------------------------------------------------------------------------------------------------------------ |
| `title`            | `string`             | `None`     | Optional text displayed at the top of the card.                                                               |
| `gap`              | `int`                | `6`        | Spacing *between* the direct children (UI Elements or Groups) within this card.                               |
| `vertical_align`   | `"top"`, `"center"`, `"bottom"` | `"top"` | How children are aligned vertically within this card (if card has extra space). |
| `horizontal_align` | `"left"`, `"center"`, `"right"`| `"left"` | How children are aligned horizontally within this card (if card has extra space). |
| `full_width`       | `bool`               | `True` ?   | Whether the card tries to take the full width available in its parent container. (Verify default)            |
| `bordered`         | `bool`               | `False` ?  | Whether the card has a visible border. (Verify availability/default)                                       |

##### Methods

| Method                             | Returns     | Description                                                               |
| :--------------------------------- | :---------- | :------------------------------------------------------------------------ |
| `create_ui_element(type, **kwargs)`| `UIElement` | Adds a UI element (Button, Text, etc.) to the card. See [UI Elements](#ui-elements). |
| `create_group(**kwargs)`           | `Group`     | Adds a layout Group to the card. See [Group Component](#group-component).      |

### Group Component

An invisible container used *only* for layout purposes, arranging multiple UI elements horizontally or vertically within a `Card` or another `Group`.

#### Class `Group`

> **Important**: Do not instantiate directly. Use `card.create_group()` or `parent_group.create_group()`.

##### Creator Method (`Card.create_group` or `Group.create_group`)

```python
# Group to place two buttons side-by-side
button_row = card.create_group(type="columns", gap=4, horizontal_align="center")
button1 = button_row.create_ui_element(UI.Button, label="OK")
button2 = button_row.create_ui_element(UI.Button, label="Cancel")

# Nested groups: Label and Input in a row, stacked vertically with another pair
config_group = card.create_group(type="rows", gap=2)

row1 = config_group.create_group(type="columns", gap=2, vertical_align="center")
row1.create_ui_element(UI.Text, content="API Key:")
row1.create_ui_element(UI.Input, placeholder="Enter key")

row2 = config_group.create_group(type="columns", gap=2, vertical_align="center")
row2.create_ui_element(UI.Text, content="Timeout:")
row2.create_ui_element(UI.Input, placeholder="Seconds", type="number")
```

##### Parameters (passed to `create_group`)

| Parameter          | Type                 | Default    | Description                                                                                                   |
| :----------------- | :------------------- | :--------- | :------------------------------------------------------------------------------------------------------------ |
| `type`             | `"columns"`, `"rows"`| `"columns"`| Layout direction for child `UI Elements` or nested `Group`s.                                                  |
| `gap`              | `int`                | `4` ?      | Spacing *between* the direct children within this group. (Verify default)                                     |
| `vertical_align`   | `"top"`, `"center"`, `"bottom"` | `"top"` | How children are aligned vertically within this group (if group has extra space). |
| `horizontal_align` | `"left"`, `"center"`, `"right"`| `"left"` | How children are aligned horizontally within this group (if group has extra space). |
| `full_width`       | `bool`               | `False`    | Whether the group should expand to the full width of its parent (`Card` or `Group`).                          |

##### Methods

| Method                             | Returns     | Description                                                               |
| :--------------------------------- | :---------- | :------------------------------------------------------------------------ |
| `create_ui_element(type, **kwargs)`| `UIElement` | Adds a UI element (Button, Text, etc.) to this group.                     |
| `create_group(**kwargs)`           | `Group`     | Adds a nested `Group` to this group.                                      |


### UI Elements

Individual components that make up the user interface.

> **Important**: Do not instantiate directly. Use `card.create_ui_element(UI.Type, ...)` or `group.create_ui_element(UI.Type, ...)`.

#### Shared Attributes & Parameters

Many UI elements share common parameters passed during creation (`create_ui_element`) and attributes that can be accessed or modified after creation.

**Common Creation Parameters:**

| Parameter   | Type     | Description                                                       |
| :---------- | :------- | :---------------------------------------------------------------- |
| `label`     | `string` | Text associated with the element (e.g., button text, input label). |
| `size`      | `string` | Controls the size (e.g., `"sm"`, `"base"`, `"lg"`). Applies to Text, Button, etc. |
| `color`     | `string` | Controls the color theme (e.g., `"primary"`, `"accent"`, `"error"`). Applies to Text, Button, etc. |
| `full_width`| `bool`   | If `True`, element tries to span the width of its container.      |
| `visible`   | `bool`   | Default `True`. If `False`, element is hidden initially. Can be changed later. |
| `disabled`  | `bool`   | Default `False`. If `True`, element is grayed out and non-interactive. Can be changed later. |

**Common Attributes (Access after creation, e.g., `my_button.visible`):**

| Attribute   | Type     | Access | Description                                                                 |
| :---------- | :------- | :----- | :-------------------------------------------------------------------------- |
| `visible`   | `bool`   | R/W    | Controls whether the element is currently shown or hidden.                  |
| `disabled`  | `bool`   | R/W    | Controls whether the element is currently interactive.                    |
| `value`     | `any`    | R/W    | The current value of the element (e.g., `Input` text, `Select` selection). |
| `onClick`   | function | W      | Assign a callback function to handle click events (Button).                 |
| `onChange`  | function | W      | Assign a callback function to handle value changes (Input, Select, Toggle). |
| `onInput`   | function | W      | Assign a callback function to handle input as it happens (Input).           |

---

#### Text

Displays static text content.

```python
# Creator: card.create_ui_element or group.create_ui_element
card.create_ui_element(UI.Text, content="This is informational text.")

# With styling
card.create_ui_element(
    UI.Text,
    content="Important Note",
    size="lg",        # 'tiny', 'sm', 'base', 'lg', 'xl', '2xl'
    weight="bold",    # 'light', 'normal', 'medium', 'semibold', 'bold'
    color="warning"   # 'default', 'primary', 'secondary', 'success', 'warning', 'error', 'accent'
)

# Accessing/Modifying after creation
status_text = card.create_ui_element(UI.Text, content="Status: OK", color="success")
# ... later ...
status_text.content = "Status: Error"
status_text.color = "error"
```

##### Parameters

| Parameter | Type     | Required | Default   | Description                     |
| :-------- | :------- | :------- | :-------- | :------------------------------ |
| `content` | `string` | Yes      |           | The text to display.            |
| `size`    | `string` | No       | `"base"`  | Font size.                      |
| `weight`  | `string` | No       | `"normal"`| Font weight.                    |
| `color`   | `string` | No       | `"default"`| Text color theme.             |
| `align`   | `string` | No       | `"left"`  | Text alignment (`left`, `center`, `right`). |

##### Attributes (Read/Write)

| Attribute | Type     | Description          |
| :-------- | :------- | :------------------- |
| `content` | `string` | The displayed text.  |
| `color`   | `string` | The text color theme.|
| `visible` | `bool`   | Visibility state.    |

---

#### Button

An interactive button that triggers an action when clicked.

```python
# Creator: card.create_ui_element or group.create_ui_element
action_button = card.create_ui_element(
    UI.Button,
    label="Perform Action",
    variant="cta",      # 'solid', 'bordered', 'ghost', 'light', 'flat', 'cta' (Call To Action)
    color="primary",    # 'default', 'primary', 'secondary', 'success', 'warning', 'error'
    size="lg",          # 'sm', 'base', 'lg'
    full_width=False
)

# Assigning a click handler
def my_action_handler():
    print("Action button clicked!", type_="INFO")
    # (Perform the action)

action_button.onClick = my_action_handler

# Modifying after creation
action_button.label = "Processing..."
action_button.disabled = True
# ... later ...
action_button.label = "Action Complete"
action_button.disabled = False
action_button.variant = "success" # Visually indicate success
```

##### Parameters

| Parameter  | Type     | Required | Default   | Description                  |
| :--------- | :------- | :------- | :-------- | :--------------------------- |
| `label`    | `string` | Yes      |           | Text displayed on the button.|
| `variant`  | `string` | No       | `"solid"` | Visual style of the button.  |
| `color`    | `string` | No       | `"default"`| Color theme of the button. |
| `size`     | `string` | No       | `"base"`  | Size of the button.        |
| `full_width`| `bool`  | No       | `False`   | Span container width?      |
| `is_loading`| `bool`  | No       | `False`   | Show a loading spinner?    |

##### Attributes (Read/Write)

| Attribute   | Type     | Description                               |
| :---------- | :------- | :---------------------------------------- |
| `label`     | `string` | The button text.                          |
| `disabled`  | `bool`   | Is the button interactive?                |
| `visible`   | `bool`   | Is the button shown?                      |
| `is_loading`| `bool`   | Show/hide the loading spinner on button.  |
| `onClick`   | function | Assign the function to call when clicked. |

---

#### Input

A field for user text input.

```python
# Creator: card.create_ui_element or group.create_ui_element
name_input = card.create_ui_element(
    UI.Input,
    label="Username",             # Label displayed above the input
    placeholder="Enter username", # Placeholder text inside the field
    type="text",                  # 'text', 'password', 'email', 'number', 'search', 'url', 'tel'
    description="Your unique username", # Small help text below the input
    clearable=True,               # Show a clear button?
    full_width=True
)

# Multiline text area
desc_input = card.create_ui_element(
    UI.Input,
    label="Description",
    placeholder="Enter details...",
    multiline=True,
    rows=5 # Approximate number of visible lines
)

# Reading the value (e.g., in a button handler)
def submit_data():
    username = name_input.value
    description = desc_input.value
    print(f"Username: {username}, Desc: {description}", type_="INFO")

# Setting the value programmatically
name_input.value = "DefaultUser"

# Event handlers for real-time feedback or validation
def on_name_change(new_value):
    print(f"Name changed to: {new_value}", type_="INFO")

def on_name_input(current_value):
     # Called on every keystroke
     if len(current_value) < 3:
         name_input.description = "Username must be at least 3 characters."
         # name_input.color = "error" # Color might apply to border/label
     else:
         name_input.description = "Username looks good!"
         # name_input.color = "success"

name_input.onChange = on_name_change # Called when input loses focus after changing
name_input.onInput = on_name_input   # Called on every keystroke
```

##### Parameters

| Parameter     | Type     | Required | Default   | Description                                     |
| :------------ | :------- | :------- | :-------- | :---------------------------------------------- |
| `label`       | `string` | No       | `None`    | Text label displayed above the input field.     |
| `placeholder` | `string` | No       | `None`    | Ghost text displayed inside when empty.         |
| `type`        | `string` | No       | `"text"`  | Input type hint (affects keyboard on mobile). |
| `description` | `string` | No       | `None`    | Small helper text displayed below the input.    |
| `multiline`   | `bool`   | No       | `False`   | If `True`, creates a multi-line textarea.     |
| `rows`        | `int`    | No       | `3` ?     | Approximate number of rows for multiline input. |
| `clearable`   | `bool`   | No       | `False`   | If `True`, shows a button to clear the input. |
| `full_width`  | `bool`   | No       | `False`   | Span container width?                         |
| `value`       | `string` | No       | `""`      | Initial value of the input field.               |

##### Attributes (Read/Write)

| Attribute   | Type     | Description                                               |
| :---------- | :------- | :-------------------------------------------------------- |
| `value`     | `string` | The current text content of the input field.            |
| `disabled`  | `bool`   | Is the input interactive?                               |
| `visible`   | `bool`   | Is the input shown?                                     |
| `description`| `string`| The helper text below the input.                          |
| `color`     | `string` | Can affect border/label color (e.g., 'error', 'success'). |
| `onChange`  | function | Handler called when value changes and focus is lost.    |
| `onInput`   | function | Handler called on every keystroke/change.               |

---

#### Image

Displays an image from a URL.

```python
# Creator: card.create_ui_element or group.create_ui_element
card.create_ui_element(
    UI.Image,
    src="https://via.placeholder.com/150", # Required: Image URL
    alt="Placeholder Image",             # Optional: Alt text (good practice)
    width=150,                           # Optional: Specify width in pixels
    height=150                           # Optional: Specify height in pixels
)

# Dynamic image
dynamic_image = card.create_ui_element(UI.Image, src="", width=100)
# ... later ...
dynamic_image.src = "https://example.com/new_image.jpg"
dynamic_image.visible = True
```

##### Parameters

| Parameter | Type     | Required | Default | Description                           |
| :-------- | :------- | :------- | :------ | :------------------------------------ |
| `src`     | `string` | Yes      |         | URL of the image file.                |
| `alt`     | `string` | No       | `""`    | Alternative text for the image.       |
| `width`   | `int`    | No       | `None`  | Width in pixels.                      |
| `height`  | `int`    | No       | `None`  | Height in pixels.                     |
| `radius`  | `string` | No       | `None`? | Corner radius ('sm', 'md', 'lg', 'full'). |

##### Attributes (Read/Write)

| Attribute | Type     | Description               |
| :-------- | :------- | :------------------------ |
| `src`     | `string` | The image URL.            |
| `alt`     | `string` | The alternative text.     |
| `visible` | `bool`   | Is the image shown?       |

---

#### Select

A dropdown menu allowing single or multiple selections.

```python
# Creator: card.create_ui_element or group.create_ui_element

# --- Data for the Select items ---
# List of dictionaries, each needs 'id' and 'title'
options = [
    {"id": "opt1", "title": "Option 1"},
    {"id": "opt2", "title": "Option 2 (Default)"},
    {"id": "opt3", "title": "Option 3 (Disabled)"},
    {"id": "opt4", "title": "Another Choice"}
]

# --- Create the Select element ---
my_select = card.create_ui_element(
    UI.Select,
    label="Choose an option:",
    items=options,                 # Required: List of option dictionaries
    mode="single",                 # 'single' or 'multiple'
    selected_items=["opt2"],       # Optional: List of initially selected item IDs
    disabled_items=["opt3"],       # Optional: List of item IDs to disable
    placeholder="Select one...",   # Optional: Text shown when nothing selected
    description="Select your preference", # Optional: Help text below
    full_width=True
)

# --- Event Handler ---
def on_selection_change(selected_ids):
    # selected_ids is a list of the IDs of the currently selected items
    if not selected_ids:
        print("Selection cleared.", type_="INFO")
        my_select.description = "Please select an option."
    else:
        print(f"Selection changed: {selected_ids}", type_="INFO")
        # For single mode, selected_ids[0] is the selection
        if my_select.mode == "single":
             # Find the title corresponding to the selected ID
             selected_title = next((item['title'] for item in options if item['id'] == selected_ids[0]), "Unknown")
             my_select.description = f"You selected: {selected_title}"

my_select.onChange = on_selection_change

# --- Modifying after creation ---
# Change items dynamically (e.g., based on another selection)
new_options = [
    {"id": "a", "title": "Choice A"},
    {"id": "b", "title": "Choice B"},
]
my_select.items = new_options
my_select.selected_items = [] # Clear selection when items change

# Get the current selection
current_selection = my_select.selected_items
print(f"Current selection is: {current_selection}", type_="INFO")
```

##### Parameters

| Parameter        | Type        | Required | Default    | Description                                                        |
| :--------------- | :---------- | :------- | :--------- | :----------------------------------------------------------------- |
| `label`          | `string`    | No       | `None`     | Label text displayed above the select.                             |
| `items`          | `list[dict]`| Yes      |            | List of item dictionaries. Each must have `"id"` and `"title"` keys. Optional `"iconUrl"`. |
| `mode`           | `string`    | No       | `"single"` | `"single"` or `"multiple"` selection mode.                         |
| `selected_items` | `list[str]` | No       | `[]`       | List of IDs of items that should be selected initially.            |
| `disabled_items` | `list[str]` | No       | `[]`       | List of IDs of items that should be disabled (non-selectable).     |
| `placeholder`    | `string`    | No       | `None`     | Text shown when no item is selected.                               |
| `description`    | `string`    | No       | `None`     | Help text displayed below the select.                              |
| `full_width`     | `bool`      | No       | `False`    | Span container width?                                            |

##### Attributes (Read/Write)

| Attribute        | Type        | Description                                                          |
| :--------------- | :---------- | :------------------------------------------------------------------- |
| `items`          | `list[dict]`| The list of item dictionaries. Can be updated dynamically.         |
| `selected_items` | `list[str]` | The list of IDs of currently selected items. Can be read or set.   |
| `disabled_items` | `list[str]` | The list of IDs of disabled items. Can be updated dynamically.     |
| `disabled`       | `bool`      | Is the entire select component interactive?                        |
| `visible`        | `bool`      | Is the select component shown?                                       |
| `onChange`       | function    | Handler called when the selection changes. Receives `selected_ids` (list) as argument. |

---

#### Dynamic UI Element Visibility

You can show or hide any UI element dynamically by changing its `.visible` attribute.

```python
# (Inside script function)
try:
    vis_tab = Tab(name="visibility_tab", title="Dynamic Visibility")
    vis_container = vis_tab.create_container()
    vis_card = vis_container.create_card(gap=4)

    # --- Toggle Button ---
    # Use script-specific prefixes
    vis_toggle_button = vis_card.create_ui_element(UI.Button, label="Hide Secret Message")

    # --- The Element to Toggle ---
    vis_secret_text = vis_card.create_ui_element(
        UI.Text,
        content="This is a secret message!",
        color="accent",
        size="lg",
        visible=True # Start visible
    )

    # --- Toggle Handler ---
    def vis_toggle_visibility():
        # Toggle the visibility state
        is_currently_visible = vis_secret_text.visible
        vis_secret_text.visible = not is_currently_visible

        # Update the button label accordingly
        if vis_secret_text.visible:
            vis_toggle_button.label = "Hide Secret Message"
        else:
            vis_toggle_button.label = "Show Secret Message"

        print(f"Secret message visibility set to: {vis_secret_text.visible}", type_="INFO")

    vis_toggle_button.onClick = vis_toggle_visibility

    vis_tab.render()
    print("Visibility UI Example loaded.", type_="SUCCESS")

except Exception as e:
    print(f"Error setting up Visibility UI: {e}", type_="ERROR")
    # Log traceback...
```

This pattern is useful for:
- Showing/hiding advanced settings.
- Displaying conditional information based on selections.
- Creating step-by-step wizards.
- Hiding elements after an action is completed.

---

#### Server and Channel Selection Example

A common UI task is selecting a Discord server and then a channel within that server. This requires dynamic updates.

```python
# Full script example for server/channel selection
@nightyScript(
    name="Server Channel Selector UI",
    author="Your Name",
    description="UI for selecting servers and channels with dynamic updates.",
    usage="Enable script and check UI tabs."
)
def server_channel_selector_ui():
    """
    SERVER CHANNEL SELECTOR UI
    --------------------------
    Provides a UI tab in Nighty to select a server, then dynamically
    populates a second dropdown with the text channels from that server
    where the self-bot has send permissions.
    """
    import asyncio # Needed potentially for bot object access readiness

    SCRIPT_PREFIX = "svch_" # Prefix for this UI script

    try:
        tab = Tab(name=f"{SCRIPT_PREFIX}tab", icon="message", title="Server & Channel Selector")
        container = tab.create_container()
        card = container.create_card(title="Selection", gap=4)

        # --- Server Selection ---
        card.create_ui_element(UI.Text, content="1. Select a Server:", weight="bold")

        # Prepare server list - ensure bot cache is ready
        # It might be better to fetch/prepare this list inside an event handler
        # if the script loads before the bot is fully ready.
        server_options = [{"id": "none", "title": "Select a server..."}]
        try:
            # Check if bot object and guilds are available
            if bot and bot.guilds:
                 for guild in bot.guilds:
                    icon_url = guild.icon.url if guild.icon else "https://cdn.discordapp.com/embed/avatars/0.png"
                    server_options.append({"id": str(guild.id), "title": guild.name, "iconUrl": icon_url})
            else:
                 print("Bot guilds not available yet for UI.", type_="WARNING")
                 # Handle case where guilds aren't ready - maybe disable select?

        except Exception as e:
            print(f"Error preparing server list: {e}", type_="ERROR")
            # Fallback or error message

        server_select = card.create_ui_element(
            UI.Select,
            items=server_options,
            selected_items=["none"],
            disabled_items=["none"],
            full_width=True,
            id=f"{SCRIPT_PREFIX}server_select" # Assigning an ID can sometimes help debugging
        )

        # --- Channel Selection (Initially Hidden/Disabled) ---
        card.create_ui_element(UI.Text, content="2. Select a Channel:", weight="bold")
        channel_select = card.create_ui_element(
            UI.Select,
            items=[{"id": "none", "title": "Select a server first..."}],
            selected_items=["none"],
            disabled_items=["none"],
            full_width=True,
            visible=False, # Start hidden
            disabled=True, # Start disabled
            id=f"{SCRIPT_PREFIX}channel_select"
        )

        # --- Status Display ---
        status_text = card.create_ui_element(UI.Text, content="Status: No server selected.", size="sm", color="secondary")

        # --- Event Handler for Server Selection ---
        def svch_on_server_change(selected_server_ids):
            if not selected_server_ids or selected_server_ids[0] == "none":
                channel_select.items = [{"id": "none", "title": "Select a server first..."}]
                channel_select.selected_items = ["none"]
                channel_select.visible = False
                channel_select.disabled = True
                status_text.content = "Status: No server selected."
                status_text.color = "secondary"
                return

            server_id_str = selected_server_ids[0]
            status_text.content = f"Status: Loading channels for server {server_id_str}..."
            status_text.color = "secondary"

            try:
                server_id = int(server_id_str)
                # Use bot.get_guild (safer than iterating guilds again)
                server = bot.get_guild(server_id)

                if not server:
                    print(f"Could not find server with ID: {server_id}", type_="ERROR")
                    channel_select.items = [{"id": "error", "title": "Error: Server not found"}]
                    channel_select.selected_items = ["error"]
                    channel_select.visible = True
                    channel_select.disabled = True
                    status_text.content = "Status: Error finding server."
                    status_text.color = "error"
                    return

                # Filter text channels where bot can send messages
                channel_options = [{"id": "none", "title": f"Select a channel in {server.name}..."}]
                valid_channels_found = False
                # Ensure server.me exists and check permissions
                me = server.me
                if not me:
                    print(f"Cannot determine 'me' in server {server.name}", type_="WARNING")
                    # Handle case where bot might not be fully recognised in the guild object?

                for channel in server.text_channels:
                     # Check permissions using server.me if available, otherwise skip permission check
                    can_send = True # Assume true if 'me' is not available
                    if me:
                        try:
                            permissions = channel.permissions_for(me)
                            can_send = permissions.send_messages
                        except Exception as perm_error:
                             print(f"Error checking permissions for channel {channel.name}: {perm_error}", type_="WARNING")
                             can_send = False # Treat as unable to send on error


                    if can_send:
                        channel_options.append({"id": str(channel.id), "title": f"#{channel.name}"})
                        valid_channels_found = True

                channel_select.items = channel_options
                channel_select.selected_items = ["none"] # Reset selection
                channel_select.disabled = not valid_channels_found # Disable if no valid channels
                channel_select.visible = True

                if valid_channels_found:
                     status_text.content = f"Status: Selected Server: {server.name}. Please select a channel."
                     status_text.color = "primary"
                else:
                     status_text.content = f"Status: Selected Server: {server.name}. No writable channels found."
                     status_text.color = "warning"


            except ValueError:
                print(f"Invalid server ID format: {server_id_str}", type_="ERROR")
                # Handle error... reset channel select
            except Exception as e:
                print(f"Error processing server selection: {e}", type_="ERROR")
                import traceback
                print(traceback.format_exc(), type_="ERROR")
                status_text.content = "Status: An error occurred."
                status_text.color = "error"
                # Reset channel select...

        # --- Event Handler for Channel Selection ---
        def svch_on_channel_change(selected_channel_ids):
             if not selected_channel_ids or selected_channel_ids[0] == "none" or selected_channel_ids[0] == "error":
                  # Keep status based on server selection or error
                  return

             channel_id_str = selected_channel_ids[0]
             # Find channel name from the current items list for display
             channel_name = next((item['title'] for item in channel_select.items if item['id'] == channel_id_str), f"ID:{channel_id_str}")
             # Find server name from the server select element
             server_id_str = server_select.selected_items[0] # Assumes single mode and server is selected
             server_name = next((item['title'] for item in server_select.items if item['id'] == server_id_str), f"ID:{server_id_str}")


             status_text.content = f"Status: Server: {server_name}, Channel: {channel_name} selected."
             status_text.color = "success"
             print(f"Final selection - Server: {server_id_str}, Channel: {channel_id_str}", type_="INFO")


        # Assign handlers
        server_select.onChange = svch_on_server_change
        channel_select.onChange = svch_on_channel_change

        tab.render()
        print(f"Server Channel Selector UI script loaded.", type_="SUCCESS")

    except Exception as e:
        print(f"Fatal error setting up Server Channel Selector UI: {e}", type_="ERROR")
        import traceback
        print(traceback.format_exc(), type_="ERROR")


# Call the function to run the script
server_channel_selector_ui()
```

---

#### Server and Channel Filtering

Often, you need to filter the list of servers or channels presented to the user based on certain criteria (e.g., only servers where the bot is admin, only text channels).

```python
# --- Helper function to filter servers ---
def filter_servers(all_guilds, criteria=None):
    """ Filters a list of guild objects based on criteria. """
    if not criteria:
        return all_guilds

    filtered = []
    for guild in all_guilds:
        # Example Criteria: Bot has Administrator permissions
        if criteria.get("needs_admin", False):
            if not guild.me or not guild.me.guild_permissions.administrator:
                continue # Skip if bot isn't admin or 'me' object not found

        # Example Criteria: Minimum member count
        min_members = criteria.get("min_members")
        if min_members is not None and guild.member_count < min_members:
            continue # Skip if server too small

        # Add more criteria checks as needed...

        filtered.append(guild)
    return filtered

# --- Helper function to filter channels ---
def filter_channels(all_channels, criteria=None):
    """ Filters a list of channel objects based on criteria. """
    if not criteria:
        return all_channels

    filtered = []
    server = all_channels[0].guild if all_channels else None # Need server context for permissions
    me = server.me if server else None

    for channel in all_channels:
        # Example Criteria: Channel type must be text
        if criteria.get("type") == "text" and not isinstance(channel, discord.TextChannel): # Use type check
             # Note: direct discord.TextChannel import forbidden, but type checking often works if objects provided by Nighty inherit correctly. Test this!
             # Alternative: check channel.type attribute if available
             # if not hasattr(channel, 'type') or str(channel.type) != 'text': continue
            continue


        # Example Criteria: Bot must be able to send messages
        if criteria.get("can_send", False):
            can_send = False
            if me:
                try:
                    can_send = channel.permissions_for(me).send_messages
                except Exception: pass # Ignore permission errors
            if not can_send:
                continue

        # Add more criteria checks...

        filtered.append(channel)
    return filtered


# --- Usage within the Server/Channel Selector UI ---
# Modify the server list preparation:
server_options = [{"id": "none", "title": "Select an admin server..."}]
try:
    if bot and bot.guilds:
        # Apply filtering criteria
        admin_servers = filter_servers(bot.guilds, criteria={"needs_admin": True})
        for guild in admin_servers:
            icon_url = guild.icon.url if guild.icon else "..."
            server_options.append({"id": str(guild.id), "title": guild.name, "iconUrl": icon_url})
    # ... rest of server select setup ...
except Exception as e: # ... error handling ...
    pass


# Modify the channel list preparation (inside svch_on_server_change):
# ... after getting `server` object ...
try:
    all_text_channels = server.text_channels
    # Apply filtering criteria
    writable_channels = filter_channels(all_text_channels, criteria={"can_send": True})

    channel_options = [{"id": "none", "title": f"Select a writable channel in {server.name}..."}]
    valid_channels_found = False
    for channel in writable_channels:
        channel_options.append({"id": str(channel.id), "title": f"#{channel.name}"})
        valid_channels_found = True
    # ... rest of channel select setup ...
except Exception as e: # ... error handling ...
    pass
```

This pattern allows creating reusable filter functions to refine the options presented in UI dropdowns based on dynamic conditions or bot permissions. Remember that direct type checking (`isinstance(channel, discord.TextChannel)`) might fail if Nighty doesn't provide objects inheriting directly from standard discord.py types; checking attributes like `channel.type == discord.ChannelType.text` (if available) might be more robust, but again, direct `discord` imports are forbidden. Adapt based on available attributes.