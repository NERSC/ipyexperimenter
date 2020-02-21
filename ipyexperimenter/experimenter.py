# Standard lib
import os
import csv
from collections import OrderedDict
# Third party
from ipywidgets import (
    VBox, HBox, Layout, GridBox, Label, Text,
    SelectMultiple, Combobox, Button, Tab, Output
)
# Local
from ipypathchooser import PathChooser

# During development, you'll want to decorate every call that observes a traitlet in
# `@output.capture` or else these methods can fail silently.
# When captured, they will display in `output` when it is rendered by evaluating it in a cell.
output = Output(layout={
    'border': '2px dotted lightgray',
    'padding': '2px',
})

class Experimenter(VBox):
    def __init__(
        self,
        default_directory=os.path.join(os.getcwd(), 'experiments'),
        default_params=None,
        title='',
        **kwargs
    ):
        # Vertical margin between blocks of UI elements
        self.vertical_spacing = 20

        # Widget serving as parent of most of Experimenter, a tabbed table
        self.Tab = Tab(
            layout=Layout(
                margin=f'{self.vertical_spacing}px 0 0 0',
            ),
        )
        self.Tab.observe(self.toggle_delete_tab_button, names='selected_index')

        # Menu displayed above the table
        self.edit_tabs_button = Button(
            description='Select visible experiments',
            tooltip='Select visible tabs',
            layout=Layout(
                width='auto',
            ),
        )
        self.edit_tabs_button.on_click(self.show_edit_tab_menu)

        self.add_tab_button = Button(
            description='New experiment',
            tooltip='Add a new experiment',
            icon='plus',
            layout=Layout(
                width='auto',
            ),
        )
        self.add_tab_button.on_click(self.add_tab)

        button_bar = HBox(
            children=[
                self.edit_tabs_button,
                self.add_tab_button,
            ],
        )

        self.edit_tab_menu = VBox(
            children=[
                Label('Visible experiments'),
                SelectMultiple(options=[], value=[]),
                Button(
                    description='Apply',
                )
            ],
            layout=Layout(
                display='none',
            ),
        )
        _, tab_select, apply_tab_selection_button = self.edit_tab_menu.children
        self.tab_select = tab_select
        apply_tab_selection_button.on_click(self.apply_tab_selection)

        self.tab_menu = VBox(
            children=[
                button_bar,
                self.edit_tab_menu,
            ],
        )

        # The maximum number of simultaenously displayed tabs
        self.max_visible_tabs = 10

        # These widgets are reused at the top of each tab
        self.save_tab_button = Button(
            description='Save',
            tooltip='Save tab',
            icon='save',
        )
        self.save_tab_button.on_click(self.save_current_tab)

        self.delete_tab_button = Button(
            description='Delete',
            tooltip='Delete tab',
            icon='trash',
        )
        self.delete_tab_button.on_click(self.delete_tab)

        # These widgets are reused at the bottom of each tab
        self.add_row_button = Button(
            description='Add a param',
            tooltip='Add a param',
            icon='plus',
        )
        self.add_row_button.on_click(self.add_row)

        self.tab_footer = HBox(
            [self.add_row_button],
            layout=Layout(
                margin=f'{self.vertical_spacing}px 0 0 0',
            ),
        )

        def make_header(header):
            """
            Create a disabled Button containing the text `header` for use in a table.
            """
            header = HBox([
                Button(
                    description=header,
                    disabled=True,
                    layout=Layout(
                        margin='0',
                        width='20px',
                        flex='1 1 auto',
                    ),
                )
            ], layout=Layout(
                border='1px solid gray',
                width='100%',
            ))
            return header

        self.headers = HBox(
            [make_header(header) for header in ['Param', 'Value', 'Comment']],
            layout=Layout(
                grid_area='headers',
            )
        )

        # These widgets appear below `self.Tab`
        self.save_all_button = Button(
            description='Save all',
            tooltip='Save all',
            icon='save',
        )
        self.save_all_button.on_click(self.save_all)

        self.run_tab_button = Button(
            description='Run tab',
            tooltip='Run tab',
            icon='play',
        )
        self.run_tab_button.on_click(self.run_tab)

        self.run_all_button = Button(
            description='Run all',
            tooltip='Run all',
            icon='forward',
        )
        self.run_all_button.on_click(self.run_all)

        self.run_bar = HBox(
            [self.save_all_button, self.run_tab_button, self.run_all_button],
            layout=Layout(
                margin=f'{self.vertical_spacing}px 0 0 0',
            ),
        )

        def load_experiments(old_path, new_path):
            # Intialize the tabs based on saved data, if any, in new_path
            self.update_available_experiments(new_path)
            self.selected_experiments = self.available_experiments[:self.max_visible_tabs]
            # A list of `VBox` widgets to be put inside a main `Tab` widget
            tabs = []
            for t, filename in enumerate(self.selected_experiments):
                row_kind = self.get_tab_kind(t)
                filepath = os.path.join(new_path, filename)
                with open(filepath) as csvfile:
                    data = list(csv.reader(csvfile, delimiter=';'))
                    # Assume headers are always Param, Value, Comment
                    rows = data[1:]
                    tab = self.make_tab(rows=rows, kind=row_kind, tab_name=filename[:-4])
                    tabs.append(tab)
                    # Populate defaults asap so other tabs can `get_params_and_comments()`
                    self.tabs = tabs
            # Default intialization
            if not self.available_experiments:
                tabs.append(self.make_tab())
                self.tabs = tabs
            self.show()

        # TODO: use the default_directory input
        # Pathchoser currently does not initialize in a way that lets it
        # initially have an item selected, which is required to do this
        self.pathchooser = PathChooser(
            chosen_path_desc='Experiments:',
            on_chosen_path_change=load_experiments,
        )

        # Initially, hide major elements until a path is chosen
        self.hide()

        # Call VBox super class __init__
        super().__init__(
            children=[
                self.pathchooser,
                self.tab_menu,
                self.Tab,
                self.run_bar,
            ],
            layout=Layout(width='auto'),
            **kwargs,
        )

    @property
    def tabs(self):
        """
        Get a list Experiementer's 'tab' widgets, which are of class `VBox`.
        """
        return list(self.Tab.children)

    @tabs.setter
    def tabs(self, tabs):
        """
        Set Experimenter's 'tab' widgets to `tabs`, updating the view.
        """
        self.Tab.children = tabs
        # Also update the displayed names on the tabs
        for t, tab in enumerate(tabs):
            tab_header, _, _ = tab.children
            tab_name, _, _ = tab_header.children
            self.Tab.set_title(t, tab_name.value)

    @property
    def experiments_directory(self):
        """
        Get the experiments directory from the pathchooser.
        """
        return self.pathchooser.chosen_path

    @experiments_directory.setter
    def experiments_directory(self, directory):
        """
        Directly set the experiments directory on the underlying pathchooser.
        """
        raise NotImplementedError

    def get_table_rows(self, index):
        """
        Present the table at tab `index` as a list of (`HBox`, `Button`)s.
        The `HBox` contains the row data as a list of `Text` or `Combobox` widgets.
        The `Button` is the button that removes the row.
        """
        tab = self.tabs[index]
        _, table, _ = tab.children
        children = table.children
        rows = [(children[i], children[i+1]) for i in range(1, len(children), 2)]
        return rows

    def get_plain_table_rows(self, index):
        """
        Present that table tab at `index` as a list of [`Param`, `Value`, `Comment`]s.
        """
        # These are tuples of widgets
        rows = [row.children for (row, remove_button) in self.get_table_rows(index)]
        # These are lists of the widget values
        plain_rows = [[param.value, value.value, comment.value] for (param, value, comment) in rows]
        return plain_rows

    def get_params_and_comments(self):
        """
        Return a list of Param values and a list of Comment values from the 'defaults' tab.
        """
        plain_rows = self.get_plain_table_rows(0)
        params = [param for (param, _, _) in plain_rows]
        comments = [comment for (_, _, comment) in plain_rows]
        return params, comments

    def get_default_comments(self):
        """
        Return a list of Comment values from the 'defaults' tab, which must always exist.
        """
        plain_rows = self.get_plain_table_rows(0)
        comments = [comment for (_, _, comments) in plain_rows]
        return comments

    def on_tab_name_change(self, change):
        """
        Update the current tab's name according to `change`.
        """
        current_tab_index = self.Tab.selected_index
        self.Tab.set_title(current_tab_index, change['new'])

    def make_tab_header(self, tab_name):
        """
        Create an `HBox` widget representing a header for describing and controlling a tab.
        """
        tab_name_input = Text(
            description='Tab name:',
            value=tab_name,
        )
        tab_name_input.observe(self.on_tab_name_change, names='value')
        children = [tab_name_input, self.save_tab_button, self.delete_tab_button]
        # Disable changing 'defaults' name
        if tab_name == 'defaults':
            children[0].disabled = True
        tab_header = HBox(
            children,
            layout=Layout(
                margin=f'{self.vertical_spacing}px 0 0 0',
            ),
        )
        return tab_header

    def make_tab(self, rows=[], kind='text', tab_name='defaults'):
        """
        Create a `VBox` widget representing `rows` as a tab with a header and footer.
        If `rows` is empty, a single blank row will be created.
        All rows on a tab have the same `kind`, either 'text' or 'combobox'.
        The tab_header will contain an input set to `tab_name`.
        """
        tab_header = self.make_tab_header(tab_name)
        children = [self.headers]
        grid_template_areas = '"headers headers headers ."'
        if not rows:
            rows = [['', '', '']]
        for r, row in enumerate(rows):
            children.append(self.make_row(r, values=row, kind=kind))
            children.append(self.make_remove_row_button(r))
            grid_template_areas += f'\n"row-{r} row-{r} row-{r} remove-row-{r}"'
        table = GridBox(
            children=children,
            layout=Layout(
                width='auto',
                margin=f'{self.vertical_spacing}px 0 0 0',
                grid_gap='0px 0px',
                grid_template_rows='repeat(auto)',
                grid_template_columns='auto auto auto 32px',
                grid_template_areas=grid_template_areas,
            ),
        )
        tab = VBox([tab_header, table, self.tab_footer])
        return tab

    def make_row(self, index, values=[], kind='text'):
        """
        Create an `HBox` representing an input row with a first input of `kind`.
        The inputs will be initialized according to `values`.
        The row will occupy a `grid_area` labeled according to `index`.
        """
        def make_text_input(value=''):
            """
            Create a `Text` input widget initialized to `value`.
            """
            return Text(
                value=value,
                layout=Layout(
                    margin='0',
                    width='20px',
                    flex='1 1 auto',
                ),
            )
        def make_combobox_input(value='', params=[]):
            """
            Create a Combobox initalized to `value` with `params` as the options.
            """
            return Combobox(
                value=value,
                placeholder='Choose a param',
                options=params,
                ensure_option=True,
                layout=Layout(
                    margin='0',
                    width='20px',
                    flex='1 1 auto',
                ),
            )
        if kind == 'combobox':
            params, _ = self.get_params_and_comments()
            first_input = make_combobox_input(value=values[0], params=params)

        else:
            first_input = make_text_input(value=values[0])
        inputs = [
            first_input,
            make_text_input(value=values[1]),
            make_text_input(value=values[2]),
        ]
        # Combobox tabs will display comments for the default params they have selected
        def on_combobox_change(change):
            """
            Update the Comment field to match the comments in 'defaults' for the selected param.
            """
            params, comments = self.get_params_and_comments()
            for p, param in enumerate(params):
                if param == change['new']:
                    inputs[2].value = comments[p]
        if kind == 'combobox':
            first_input.observe(on_combobox_change, names='value')
            inputs[2].disabled = True
        return HBox(
            inputs,
            layout=Layout(
                grid_area=f'row-{index}',
            ),
        )

    def remove_row(self, row_index):
        """
        Return a function that removes the row at `row_index` from the selected tab.
        """
        def remove(button):
            current_tab_index = self.Tab.selected_index
            rows = self.get_plain_table_rows(current_tab_index)
            rows = rows[:row_index] + rows[row_index + 1:]
            tab_name = self.get_tab_name(current_tab_index)
            tab_kind = self.get_tab_kind(current_tab_index)
            new_tab = self.make_tab(rows=rows, kind=tab_kind, tab_name=tab_name)
            self.tabs = self.tabs[:current_tab_index] + [new_tab] + self.tabs[current_tab_index + 1:]
        return remove

    def make_remove_row_button(self, index):
        """
        Create a `Button` that removes the row at `index` on the selected tab.
        """
        remove = Button(
            tooltip='Delete row',
            icon='remove',
            layout=Layout(
                margin='0',
                width='auto',
                grid_area=f'remove-row-{index}',
            ),
        )
        remove.on_click(self.remove_row(index))
        return remove

    def get_tab_kind(self, index):
        """
        Return 'combobox' if index > 0 else 'text'.
        """
        return 'combobox' if index > 0 else 'text'

    def default_tab_name(self, index):
        return 'defaults' if index == 0 else f'exp{index:03}'

    def add_tab(self, button):
        """
        Create and add a new tab.
        """
        index = len(self.tabs)
        tab = self.make_tab(kind=self.get_tab_kind(index), tab_name=self.default_tab_name(index))
        self.tabs = self.tabs + [tab]

    def get_tab_name(self, index):
        """
        Return the name of the tab at `index`.
        """
        tab = self.tabs[index]
        tab_header, _, _  = tab.children
        tab_name, _, _ = tab_header.children
        return tab_name.value

    def add_row(self, button):
        """
        Create and add a row (an `HBox` of inputs) to the current tab.
        """
        current_tab_index = self.Tab.selected_index
        tab_name = self.get_tab_name(current_tab_index)
        tab_kind = self.get_tab_kind(current_tab_index)
        rows = self.get_plain_table_rows(current_tab_index)
        rows.append(['', '', ''])
        index = len(rows) + 1
        new_tab = self.make_tab(rows=rows, kind=tab_kind, tab_name=tab_name)
        self.tabs = self.tabs[:current_tab_index] + [new_tab] + self.tabs[current_tab_index + 1:]

    def save_tab(self, index):
        """
        Save the tab data at index.
        """
        tab_name = self.get_tab_name(index)
        rows = self.get_plain_table_rows(index)
        filepath = os.path.join(self.experiments_directory, f'{tab_name}.csv')
        with open(filepath, 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(['Param', 'Value', 'Comment'])
            for row in rows:
                writer.writerow(row)

    def save_current_tab(self, button):
        """
        Save the current tab's data as a csv file.
        """
        current_tab_index = self.Tab.selected_index
        self.save_tab(current_tab_index)

    def save_all(self, button):
        """
        Save all tab's data as csv files.
        """
        # TODO: delete any csvs in the folder before saving all
        for i, tab in enumerate(self.tabs):
            self.save_tab(i)

    def delete_tab(self, button):
        """
        Delete the current tab. Data removed from disk only on "save all".
        """
        current_tab_index = self.Tab.selected_index
        self.tabs = self.tabs[:current_tab_index] + self.tabs[current_tab_index + 1:]

    def apply_tab_selection(self, button):
        """
        Select and display the tabs selected in `self.tab_select`.
        """
        self.edit_tab_menu.layout.display = 'none'

    def show_edit_tab_menu(self, button):
        """
        Toggle 'on' the visibility of `self.edit_tab_menu`.
        """
        self.edit_tab_menu.layout.display = None

    def update_available_experiments(self, directory):
        """
        Scan the input directory to determine the available experiments.
        """
        csvs = filter(lambda f: f.endswith('.csv'), os.listdir(directory))
        def defaults_first(experiment_name):
            return '' if experiment_name == 'defaults.csv' else experiment_name
        experiment_names = sorted(csvs, key=defaults_first)
        self.available_experiments = list(experiment_names)
        self.tab_select.options = self.available_experiments

    def toggle_delete_tab_button(self, change):
        """
        Toggle whether the delete tab button is enabled or disabled when the `tab_index` changes.
        """
        tab_name = self.get_tab_name(change.new)
        self.delete_tab_button.disabled = tab_name == 'defaults'

    def show(self):
        """
        Show the components of the widget aside from the Pathchooser.
        """
        self.tab_menu.layout.display = None
        self.Tab.layout.display = None
        self.run_bar.layout.display = None

    def hide(self):
        """
        Hide the components of the widget other than the Pathchooser.
        """
        self.tab_menu.layout.display = 'none'
        self.Tab.layout.display = 'none'
        self.run_bar.layout.display = 'none'

    def run_tab(self):
        """
        Run the selected notebook(s) with the params in the current tab.
        """
        raise NotImplementedError

    def run_all(self):
        """
        Run the selected notebook(s) with the parms from every tab.
        """
        raise NotImplementedError
