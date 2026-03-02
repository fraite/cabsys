# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import cabsys
import cabsys.gui.project_viewer as project_viewer


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    my_project = cabsys.Project(name='my project')
    project_viewer.ProjectViewer(my_project)

