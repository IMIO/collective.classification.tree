*** Settings ***
Documentation  The categories: add, add a sub-category, edit, delete.
Resource  classification.robot
Test Setup  Open the site as a manager
Test Teardown  Close the browser


*** Test Cases ***
Add a category
    A classification container
    Click the content action  classification\\.tree\\.add
    Fill the category form  001  First
    Click button  css=#form-buttons-add
    The status message contains  Category added
    The page title is  001 - First

Add a sub-category from a category
    ${container_url}=  A classification container
    ${first_url}=  Add a category  ${container_url}  001  First
    Add a category  ${first_url}  001.1  Sub
    The page title is  001.1 - Sub
    Go to  ${first_url}
    The listing shows the category  001.1

Edit a category
    ${container_url}=  A classification container
    ${first_url}=  Add a category  ${container_url}  001  First
    Go to  ${first_url}/edit
    Input text  css=#form-widgets-title  First edited
    Click button  css=#form-buttons-save
    The status message contains  Changes saved
    The page title is  001 - First edited

Delete a category
    ${container_url}=  A classification container
    ${first_url}=  Add a category  ${container_url}  001  First
    Add a category  ${container_url}  002  Second
    Go to  ${first_url}/delete_confirmation
    Click button  css=#form-buttons-Cancel
    The page title is  001 - First
    Go to  ${first_url}/delete_confirmation
    Click button  css=#form-buttons-Delete
    The status message contains  001 - First has been deleted.
    Location should be  ${container_url}
    The listing shows the category  002
    The listing does not show the category  001
