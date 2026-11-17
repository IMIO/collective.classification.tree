*** Settings ***
Documentation  The classification container: creation, actions, listing of the categories, cache refresh.
Resource  classification.robot
Test Setup  Open the site as a manager
Test Teardown  Close the browser


*** Test Cases ***
Create a classification container
    Go to  ${PLONE_URL}/++add++ClassificationContainer
    Input text  css=#form-widgets-IBasic-title  My tree
    Click button  css=#form-buttons-save
    The status message contains  Item created
    The page title is  My tree
    Location should contain  ${PLONE_URL}/my-tree
    Page should contain element  css=table#table.tree-listing

The Actions menu of the container shows import, add category and refresh cache
    A classification container
    The content actions are available  classification\\.import  classification\\.tree\\.add
    ...  classification\\.tree\\.refresh_cache

The listing of the container shows its categories
    ${container_url}=  A classification container
    ${first_url}=  Add a category  ${container_url}  001  First
    Add a category  ${container_url}  002  Second
    Go to  ${container_url}
    The listing shows the category  001
    The listing shows the category  002
    Search the listing  Second
    The listing does not show the category  001
    The listing shows the category  002
    Go to  ${container_url}
    Click link  First
    Location should be  ${first_url}
    The page title is  001 - First

Refresh cache redirects to the container
    ${container_url}=  A classification container
    Click the content action  classification\\.tree\\.refresh_cache
    Location should be  ${container_url}
    The page title is  Tree

The listing of the container shows its categories to a site administrator
    ${container_url}=  A classification container
    Add a category  ${container_url}  001  First
    Enable autologin as  Site Administrator
    Go to  ${container_url}
    The listing shows the category  001
