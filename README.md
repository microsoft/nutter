
# Nutter


- [Overview](#overview)
- [Nutter Runner](#nutter-runner)
  * [Cluster Installation](#cluster-installation)
  * [Nutter Fixture](#nutter-fixture)
  * [Test Cases](#test-cases)
  * [before_all and after_all](#before-all-and-after-all)
- [Nutter CLI](#nutter-cli)
  * [Getting Started with the Nutter CLI](#getting-started-with-the-nutter-cli)
  * [Listing Test Notebooks](#listing-test-notebooks)
  * [Executing Test Notebooks](#executing-test-notebooks)
  * [Run single test notebook](#run-single-test-notebook)
  * [Run multiple tests notebooks](#run-multiple-tests-notebooks)
  * [Parallel Execution](#parallel-execution)
- [Nutter CLI Syntax and Flags](#nutter-cli-syntax-and-flags)
  * [Run Command](#run-command)
  * [List Command](#list-command)
- [Integrating Nutter with Azure DevOps](#integrating-nutter-with-azure-devops)
- [Contributing](#contributing)
  * [Contribution Tips](#contribution-tips)
  * [Contribution Guidelines](#contribution-guidelines)
## Overview

The Nutter framework makes it easy to test Databricks notebooks.  The framework enables a simple inner dev loop and easily integrates with Azure DevOps Build/Release pipelines, among others.  When data or ML engineers want to test a notebook, they simply create a test notebook called *test_*<notebook_under_test>.

Nutter has 2 main components:

1. Nutter Runner - this is the server-side component that is installed as a library on the Databricks cluster
2. Nutter CLI - this is the client CLI that can be installed both on a developers laptop and on a build agent

The tests can be run from within that notebook or executed from the Nutter CLI, useful for integrating into Build/Release pipelines.

## Nutter Runner

### Cluster Installation

The Nutter Runner can be installed as a cluster library, via PyPI.

![](cluster_install.PNG?raw=true)

For more information about installing libraries on a cluster, review [Install a library on a cluster](https://docs.microsoft.com/en-us/azure/databricks/libraries#--install-a-library-on-a-cluster).

### Nutter Fixture

The Nutter Runner is simply a base Python class, NutterFixture, that test fixtures implement.  The runner runtime is a module you can use once you install Nutter on the Databricks cluster.  The NutterFixture base class can then be imported in a test notebook and implemented by a test fixture:

``` Python
from runtime.nutterfixture import NutterFixture, tag
class MyTestFixture(NutterFixture):
   …
```

To run the tests:

``` Python
result = MyTestFixture().execute_tests()
```

To view the results from within the test notebook:

``` Python
print(result.to_string())
```

To return the test results to the Nutter CLI:

``` Python
result.exit(dbutils)
```

__Note:__ The call to result.exit, behind the scenes calls dbutils.notebook.exit, passing the serialized TestResults back to the CLI.  At the current time, print statements do not work when dbutils.notebook.exit is called in a notebook, even if they are written prior to the call.  For this reason, it is required to *temporarily* comment out result.exit(dbutils) when running the tests locally.

The following defines a single test fixture named 'MyTestFixture' that has 1 TestCase named 'test_name':

``` Python
from runtime.nutterfixture import NutterFixture, tag
class MyTestFixture(NutterFixture):
   def run_test_name(self):
      dbutils.notebook.run('notebook_under_test', 600, args)

   def assertion_test_name(self):
      some_tbl = sqlContext.sql('SELECT COUNT(*) AS total FROM sometable')
      first_row = some_tbl.first()
      assert (first_row[0] == 1)

result = MyTestFixture().execute_tests()
print(result.to_string())
# Comment out the next line (result.exit(dbutils)) to see the test result report from within the notebook
result.exit(dbutils)

```

To execute the test from within the test notebook, simply run the cell containing the above code.  At the current time, in order to see the below test result, you will have to comment out the call to result.exit(dbutils).  That call is required to send the results, if the test is run from the CLI, so do not forget to uncomment after locally testing.

``` Python
Notebook: (local) - Lifecycle State: N/A, Result: N/A
============================================================
PASSING TESTS
------------------------------------------------------------
test_name (19.43149897100011 seconds)


============================================================
```

### Test Cases

A test fixture can contain 1 or mote test cases.  Test cases are discovered when execute_tests() is called on the test fixture.  Every test case is comprised of 1 required and 3 optional methods and are discovered by the following convention: prefix_testname, where valid prefixes are: before_, run_, assertion_, and after_.  A test fixture that has run_fred and assertion_fred methods has 1 test case called 'fred'.  The following are details about test case methods:  

* _before\_(testname)_ - (optional) - if provided, is run prior to the 'run_' method.  This method can be used to setup any test pre-conditions

* _run\_(testname)_ - (optional) - if provider, is run after 'before_' if before was provided, otherwise run first.  This method is typically used to run the notebook under test

* _assertion\_(testname)_ (required) - run after 'run_', if run was provided.  This method typically contains the test assertions

__Note:__  You can assert test scenarios using the standard ``` assert ``` statement or the assertion capabilities from a package of your choice.

* _after\_(testname)_ (optional) - if provided, run after 'assertion_'.  This method typically is used to clean up any test data used by the test

A test fixture can have multiple test cases.  The following example shows a fixture called MultiTestFixture with 2 test cases: 'test_case_1' and 'test_case_2' (assertion code omitted for brevity):

``` Python
from runtime.nutterfixture import NutterFixture, tag
class MultiTestFixture(NutterFixture):
   def run_test_case_1(self):
      dbutils.notebook.run('notebook_under_test', 600, args)

   def assertion_test_case_1(self):
     …

   def run_test_case_2(self):
      dbutils.notebook.run('notebook_under_test', 600, args)

   def assertion_test_case_2(self):
     …

result = MultiTestFixture().execute_tests()
print(result.to_string())
#result.exit(dbutils)
```

### before_all and after_all

Test Fixtures also can have a before_all() method which is run prior to all tests and an after_all() which is run after all tests.

``` Python
from runtime.nutterfixture import NutterFixture, tag
class MultiTestFixture(NutterFixture):
   def before_all(self):
      …

   def run_test_case_1(self):
      dbutils.notebook.run('notebook_under_test', 600, args)

   def assertion_test_case_1(self):
     …

   def after_all(self):
      …
```

### Multiple test assertions pattern with before_all

It is possible to support multiple assertions for a test by implementing a before_all method, no run methods and multiple assertion methods.  In this pattern, the before_all method runs the notebook under test.  There are no run methods.  The assertion methods simply assert against what was done in before_all. 

``` Python
from runtime.nutterfixture import NutterFixture, tag
class MultiTestFixture(NutterFixture):
   def before_all(self):
     dbutils.notebook.run('notebook_under_test', 600, args) 
      …

   def assertion_test_case_1(self):
      …

   def assertion_test_case_2(self):
     …

   def after_all(self):
      …
```

### Guaranteed test order

After test cases are loaded, Nutter uses a sorted dictionary to order them by name.  Therefore test cases will be executed in alphabetical order.

### Sharing state between test cases

It is possible to share state across test cases via instance variables.  Generally, these should be set in the constructor.  Please see below:

```Python
class TestFixture(NutterFixture):
  def __init__(self):
    self.file = '/data/myfile'
    NutterFixture.__init__(self)
```

## Nutter CLI

The Nutter CLI is a command line interface that allows you to execute and list tests via a Command Prompt.

### Getting Started with the Nutter CLI

Install the Nutter CLI

``` bash
pip install nutter
```

__Note:__ It's recommended to install the Nutter CLI in a virtual environment.

Set the environment variables.

Linux

``` bash
export DATABRICKS_HOST=<HOST>
export DATABRICKS_TOKEN=<TOKEN>
```

Windows PowerShell

``` cmd
$env DATABRICKS_HOST="HOST"
$env DATABRICKS_TOKEN="TOKEN"
```

__Note:__ For more information about personal access tokens review  [Databricks API Authentication](https://docs.azuredatabricks.net/dev-tools/api/latest/authentication.html).

### Listing Test Notebooks

The following command list all test notebooks in the folder ```/dataload```

``` bash
nutter list /dataload
```

__Note:__ The Nutter CLI lists only tests notebooks that follow the naming convention for Nutter test notebooks.

By default the Nutter CLI lists test notebooks in the folder ignoring sub-folders. 

You can list all test notebooks in the folder structure using the ```--recursive```  flag.

``` bash
nutter list /dataload --recursive
```

### Executing Test Notebooks

The ```run``` command  schedules the execution of test notebooks and waits for their result.

### Run single test notebook

The following command executes the test notebook ```/dataload/test_sourceLoad``` in the cluster ```0123-12334-tonedabc```.

```bash
nutter run dataload/test_sourceLoad --cluster_id 0123-12334-tonedabc
```

__Note:__ In Azure Databricks you can get the cluster ID by selecting a cluster name from the Clusters tab and clicking on the JSON view.

### Run multiple tests notebooks

The Nutter CLI supports the execution of multiple notebooks via name pattern matching. The Nutter CLI applies the pattern to the name of test notebook **without** the *test_* prefix. The CLI also expects that you omit the prefix when specifying the pattern.


Say the *dataload* folder has the following test notebooks: *test_srcLoad* and *test_srcValidation*. The following command will result in the execution of both tests.

```bash
nutter run dataload/src* --cluster_id 0123-12334-tonedabc
```

In addition, if you have tests in a hierarchical folder structure, you can recursively execute all tests by setting the ```--recursive``` flag.

The following command will execute all tests in the folder structure within the folder *dataload*.

```bash
nutter run dataload/ --cluster_id 0123-12334-tonedabc --recursive
```

### Parallel Execution

By default the Nutter CLI executes the test notebooks sequentially. The execution is a blocking operation that returns when the job reaches a terminal state or when the timeout expires.

You can execute mutilple notebooks in parallel by increasing the level of parallelism. The flag  ```--max_parallel_tests``` controls the level of parallelism and determines the maximum number of tests that will be executed at the same time.

The following command executes all the tests in the *dataload* folder structure, and submits and waits for the execution of at the most 2 tests in parallel.

```bash
nutter run dataload/ --cluster_id 0123-12334-tonedabc --recursive --max_parallel_tests 2
```

__Note:__ Running tests notebooks in parallel introduces the risk of data race conditions when two or more tests notebooks modify the same tables or files at the same time. Before increasing the level of parallelism make sure that your tests cases modify only tables or files that are used or referenced within the scope of the test notebook.

## Nutter CLI Syntax and Flags

### Run Command

``` bash
SYNOPSIS
    nutter run TEST_PATTERN CLUSTER_ID <flags>

POSITIONAL ARGUMENTS
    TEST_PATTERN
    CLUSTER_ID
```

```  bash
FLAGS
    --timeout              Execution timeout in seconds. Integer value. Default is 120
    --junit_report         Create a JUnit XML report from the test results.
    --tags_report          Create a CSV report from the test results that includes the test cases tags.
    --max_parallel_tests   Sets the level of parallelism for test notebook execution.
    --recursive            Executes all tests in the hierarchical folder structure. 
```

__Note:__ You can also use flags syntax for POSITIONAL ARGUMENTS

### List Command

``` bash
NAME
    nutter list

SYNOPSIS
    nutter list PATH <flags>

POSITIONAL ARGUMENTS
    PATH
```

``` bash
FLAGS
    --recursive         Lists all tests in the hierarchical folder structure.
```

__Note:__ You can also use flags syntax for POSITIONAL ARGUMENTS

## Integrating Nutter with Azure DevOps

You can run the Nutter CLI within an Azure DevOps pipeline. The Nutter CLI will exit with non-zero code when a test case fails or the execution of the test notebook is not successful.

The following Azure DevOps pipeline installs nutter, recursively executes all tests in the workspace folder ```/Shared/ ```  and publishes the test results.

__Note:__ The pipeline expects the Databricks cluster, host and API token as pipeline varibles.



```yaml
# Starter Nutter pipeline

trigger:
- develop

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.5'

- script: |
    pip install nutter
  displayName: 'Install Nutter'

- script: |
    nutter run /Shared/ $CLUSTER --recursive --junit_report
  displayName: 'Execute Nutter'
  env:
      CLUSTER: $(clusterID)
      DATABRICKS_HOST: $(databricks_host)
      DATABRICKS_TOKEN: $(databricks_token)

- task: PublishTestResults@2
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: '**/test-*.xml'
    testRunTitle: 'Publish Nutter results'
  condition: succeededOrFailed()
```

In some scenarios, the notebooks under tests must be executed in a  pre-configured test workspace, other than the development one, that contains the necessary pre-requisites such as test data, tables or mounted points. In such scenarios, you can use the pipeline to deploy the notebooks to the test workspace before executing the tests with Nutter.

The following sample pipeline uses the Databricks CLI to publish the notebooks from triggering branch to the test workspace. 


```yaml
# Starter Nutter pipeline

trigger:
- develop

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.5'

- task: configuredatabricks@0
  displayName: 'Configure Databricks CLI'
  inputs:
    url: $(databricks_host)
    token: $(databricks_token)

- task: deploynotebooks@0
  displayName: 'Publish notebooks to test workspace'
  inputs:
    notebooksFolderPath: '$(System.DefaultWorkingDirectory)/notebooks/nutter'
    workspaceFolder: '/Shared/nutter'

- script: |
    pip install nutter
  displayName: 'Install Nutter'

- script: |
    nutter run /Shared/ $CLUSTER --recursive --junit_report
  displayName: 'Execute Nutter'
  env:
      CLUSTER: $(clusterID)
      DATABRICKS_HOST: $(databricks_host)
      DATABRICKS_TOKEN: $(databricks_token)

- task: PublishTestResults@2
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: '**/test-*.xml'
    testRunTitle: 'Publish Nutter results'
  condition: succeededOrFailed()
```

## Contributing

### Contribution Tips

 - There's a known issue with VS Code and the lastest version of pytest.
   - Please make sure that you install pytest 5.0.1
   - If you installed pytest using VS Code, then you are likely using the incorrect version. Run the following command to fix it:

``` Python
pip install --force-reinstall pytest==5.0.1
 ```

Creating the wheel file and manually test wheel locally

1. Change directory to the root that contains setup.py
2. Update the version in the setup.py
3. Run the following command: python3 setup.py sdist bdist_wheel
4. (optional) Install the wheel locally by running: python3 -m pip install <path-to-whl-file>

### Contribution Guidelines

If you would like to become an active contributor to this project please follow the instructions provided in [Microsoft Azure Projects Contribution Guidelines](http://azure.github.io/guidelines/).

-----
This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.