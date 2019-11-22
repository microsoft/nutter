

# Nutter

## Overview
The Nutter framework makes it easy to test Databricks notebooks.  The framework enables a simple inner dev loop, but also easily integrates with Azure DevOps Build/Release pipelines, among others.  When data or ML engineers want to test a notebook, they simply create a test notebook called *test_*<notebook_under_test>.  


The tests can be run from within that notebook or executed from the Nutter CLI, useful for integrating into Build/Release pipelines.

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

## Components
Nutter has 2 main components:
1. Nutter Runner - this is the server-side component that is installed as a library on the Databricks cluster
2. Nutter CLI - this is the client CLI that can be installed both on a developers laptop and on a build agent

## Nutter Runner
The Nutter Runner is simply a base Python class, NutterFixture, that test fixtures implement.  The runner is installed as a library on the Databricks cluster.  The NutterFixture base class can then be imported in a test notebook and implemented by a test fixture:
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

### Test Cases
A test fixture can contain 1 or mote test cases.  Test cases are discovered when execute_tests() is called on the test fixture.  Every test case is comprised of 2 required and 2 optional methods and are discovered by the following convention: prefix_testname, where valid prefixes are: before_, run_, assertion_, and after_.  A test fixture that has run_fred and assertion_fred methods has 1 test case called 'fred'.  The following are details about test case methods:  

* before_(testname) - (optional) - if provided, is run prior to the 'run_' method.  This method can be used to setup any test pre-conditions
* run_(testname) - (required) - run after 'before_' if before was provided, otherwise run first.  This method typically runs the notebook under test
* assertion_(testname) (required) - run after 'run_'.  This method typically contains the test assertions
* after_(testname) (optional) - if provided, run after 'assertion_'.  This method typically is used to clean up any test data used by the test

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
result.exit(dbutils)
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

### Installing the Nutter Runner on Azure Databricks
Perform the following steps to install the Nutter wheel file on your Azure Databricks cluster:
1. Open your Azure Databricks workspace
2. Click on the 'Clusters' link (on the left)
3. Click on the cluster you wish to install Nutter on
4. Click 'Libraries' (at the top)
5. Click 'Install New'
6. Drag the Nutter whl file 

## Nutter CLI

### 
### Getting Started
Install the Nutter CLI from the source.

``` bash
pip install setuptools
git clone https://github.com/microsoft/nutter
cd nutter
python setup.py bdist_wheel
cd dist
pip install nutter-<LATEST_VERSION>-py3-none-any.whl
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

## Examples

### 1. Listing Test Notebooks

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

### 2. Executing Test Notebooks

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

*Run Command*

```
SYNOPSIS
    nutter run TEST_PATTERN CLUSTER_ID <flags>

POSITIONAL ARGUMENTS
    TEST_PATTERN
    CLUSTER_ID
```

```
FLAGS
    --timeout              Execution timeout. Default 120s
    --junit_report         Create a JUnit XML report from the test results.
    --tags_report          Create a CSV report from the test results that includes the test cases tags.
    --max_parallel_tests   Sets the level of parallelism for test notebook execution.
    --recursive            Executes all tests in the hierarchical folder structure. 
```   

__Note:__ You can also use flags syntax for POSITIONAL ARGUMENTS

*List Command*

```
NAME
    nutter list

SYNOPSIS
    nutter list PATH <flags>

POSITIONAL ARGUMENTS
    PATH
```

```
FLAGS
    --recursive         Lists all tests in the hierarchical folder structure.
```

__Note:__ You can also use flags syntax for POSITIONAL ARGUMENTS

## Integrating Nutter with Azure DevOps

You can run the Nutter CLI within an Azure DevOps pipeline. The Nutter CLI will exit with non-zero code when a test case fails or the execution of the test notebook is not successful.

For full integration of the test results with Azure DevOps you can set the flag ```--junit_report```. When this flag is set, the Nutter CLI outputs the results of the tests cases as a JUnit XML compliant file.

# Contributing
## Using VS Code
- There's a known issue with VS Code and the lastest version of pytest.
 - Please make sure that you install pytest 5.0.1
 - If you installed pytest using VS Code, then you are likely using the incorrect version. Run the following command to fix it:
``` Python
pip install --force-reinstall pytest==5.0.1
 ```

## Creating the wheel file and manually test wheel locally
1. Change directory to the root that contains setup.py
2. Update the version in the setup.py
3. Run the following command: python3 setup.py sdist bdist_wheel
4. (optional) Install the wheel locally by running: python3 -m pip install <path-to-whl-file>
