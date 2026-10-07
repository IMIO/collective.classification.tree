*** Settings ***
Documentation  Import of the categories from a CSV file, in 2 steps.
Resource  classification.robot
Test Setup  Open the site as a manager
Test Teardown  Close the browser


*** Test Cases ***
Import a CSV file in 2 steps
    ${container_url}=  A classification container
    Click the content action  classification\\.import
    Choose file  css=#form-widgets-source-input  ${CURDIR}/categories.csv
    Select from list by value  css=#form-widgets-separator  ;
    Click button  css=#form-buttons-continue
    Page should contain  Sample data : '1', '1.1'
    Select from list by value  css=#form-widgets-column_0  identifier
    Select from list by value  css=#form-widgets-column_1  title
    Click button  css=#form-buttons-import
    The status message contains  Import completed in
    Location should be  ${container_url}
    The listing shows the category  1
    The listing shows the category  1.1
    The listing shows the category  2
