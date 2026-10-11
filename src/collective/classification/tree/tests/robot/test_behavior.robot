*** Settings ***
Documentation  The classification categories behavior: field of a classified content.
...            Plone 6 only (select2 keywords of ui_plone6.robot).
Resource  classification.robot
Test Setup  Open the site as a manager
Test Teardown  Close the browser


*** Test Cases ***
Classify a content in a category
    ${container_url}=  A classification container
    Add a category  ${container_url}  001  First
    Create content  type=ClassifiedItem  id=mail  title=Mail
    Go to  ${PLONE_URL}/mail/edit
    Select in the multi select2 widget  IClassificationCategory-classification_categories  001 - First
    Click button  css=#form-buttons-save
    The status message contains  Changes saved
    The categories field shows  001 - First
    Go to  ${PLONE_URL}/mail/edit
    The select2 widget contains  IClassificationCategory-classification_categories  001 - First
