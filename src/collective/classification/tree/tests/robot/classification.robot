*** Settings ***
Documentation  collective.classification.tree keywords, built on the ui_plone${PLONE_MAJOR}.robot keywords.
...            Robot Framework 3.0 syntax (shared with the Plone 4.3 environment).
Resource  ui_plone${PLONE_MAJOR}.robot
Library  String


*** Keywords ***
Open the site as a manager
    Open test browser
    Enable autologin as  Manager

Close the browser
    Run keyword if test failed  Capture page screenshot
    Close all browsers

The content actions are available
    [Documentation]  The page is reloaded before each check: a second click on the Actions menu closes it
    [Arguments]  @{action_ids}
    FOR  ${action_id}  IN  @{action_ids}
        Reload page
        The content action is available  ${action_id}
    END

A classification container
    [Documentation]  Created by the remote library, returns its url
    Create content  type=ClassificationContainer  id=tree  title=Tree
    Go to  ${PLONE_URL}/tree
    [Return]  ${PLONE_URL}/tree

Add a category
    [Documentation]  With the add form of the container or of the parent category, returns the category url
    [Arguments]  ${parent_url}  ${identifier}  ${title}
    Go to  ${parent_url}/add-ClassificationCategory
    Fill the category form  ${identifier}  ${title}
    Click button  css=#form-buttons-add
    The status message contains  Category added
    ${url}=  Get location
    ${url}=  Replace string using regexp  ${url}  /view$  ${EMPTY}
    [Return]  ${url}

Fill the category form
    [Arguments]  ${identifier}  ${title}
    Input text  css=#form-widgets-identifier  ${identifier}
    Input text  css=#form-widgets-title  ${title}

The page title is
    [Arguments]  ${title}
    Element text should be  css=h1.documentFirstHeading  ${title}

The listing shows the category
    [Arguments]  ${identifier}
    Wait until page contains element  xpath=//table[@id="table"]//td/a[text()="${identifier}"]

The listing does not show the category
    [Documentation]  Call it after a check that the listing is loaded
    [Arguments]  ${identifier}
    Wait until page does not contain element  xpath=//table[@id="table"]//td/a[text()="${identifier}"]

Search the listing
    [Arguments]  ${text}
    Input text  css=#table_filter input  ${text}

The categories field shows
    [Documentation]  Value of the classification categories field in the view of the content
    [Arguments]  ${text}
    Element should contain  css=#form-widgets-IClassificationCategory-classification_categories  ${text}
