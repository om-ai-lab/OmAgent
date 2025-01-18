# Contributing to OmAgent

**We welcome contributions from everyone!** If you're interested in contributing to OmAgent, please follow these guidelines.

## Principles
All contributions should start with an issue. You can start your contribution by replying to an [existing issue](https://github.com/om-ai-lab/OmAgent/issues?q=is%3Aissue+is%3Aopen+), or by creating [a new one](https://github.com/om-ai-lab/OmAgent/issues/new).  
Please describe your contribution in the issue as detailed as possible, including the contribution point, reason, implementation method, etc. The project manager will communicate with you as soon as possible according to the description of the issue and assign the task to you.

We classify contributions into two categories: **new feature** and **optimization**.

### New Feature
If you want to contribute a new feature, please explain in detail the function of the feature and your technical approach in the issue. We provide three possible entry points for you:

1. Add a new feature module to OmAgent. For example, support a new large language model, a new memory, a new client type, a new tool, etc.

2. Add a new application to OmAgent. This can be an example application to guide new developers; it can also be an application with practical value; or it can be a reproduction of the content of a paper.  
All applications should be placed under the ```example``` path. An application should contain the worker code, the worker configuration files, the compilation script used to generate the container configuration file template, the program's runtime entry script, and the application's description file, README.md. A typical directory for a simple single-workflow agent is as follows:
   ```
   examples/step1_simpleVQA
   ├── agent   # Where to put worker codes
   │   ├── input_interface
   │   │   ├── __init__.py
   │   │   └── input_interface.py
   │   └── simple_vqa
   │       ├── __init__.py
   │       └── simple_vqa.py
   ├── compile_container.py    # Compilation script
   ├── configs # Where to put worker config files
   │   ├── llms
   │   │   └── gpt.yml
   │   └── workers
   │       └── simple_vqa.yaml
   ├── __init__.py
   ├── README.md
   ├── run_app.py
   ├── run_cli.py
   └── run_webpage.py
   ```

1. Add an agent operator to OmAgent. An agent operator refers to a general-purpose agent logic module, which can be a worker or a sub-workflow.  
All agent operators should be placed under the ```omagent-core/src/omagent_core/advanced_components``` path. Single functional nodes can be placed in the ```omagent-core/src/omagent_core/advanced_components/worker``` directory, and these workers should have high generalizability to be used in different functional scenarios. Similarly, workflows with high generalizability can be placed in the ```omagent-core/src/omagent_core/advanced_components/workflow``` directory and can be used as sub-workflows by other developers.   
The file structure of the workflow operator should be similar to the simple single-workflow agent mentioned above. The major difference is that the workflow operator does not require an entry script, but needs a workflow.py file containing a ```ConductorWorkflow``` object. In addition, the README file of the workflow operator should describe the input and output parameters of the workflow, as well as their types.
   ```
   Inputs:
   | Name     | Type | Required | Description |
   | -------- | ----- | ----- | ---- |
   | user_name | str | true |  The name of the user |
   ```
   When submitting an agent operator, you should also submit an example under the `example` directory to demonstrate how to use the operator. The example should include:

   1. A complete application that uses the operator
   2. Clear documentation explaining how to use the operator
   3. Sample input/output to help users understand the operator's behavior

   For example, if you submit a workflow operator for task decomposition, you should:

   1. Place the operator code under `omagent-core/src/omagent_core/advanced_components/worker/new_worker_operator/`
   2. Create an example under `examples/new_worker_operator_demo/` showing how to use it

   The example helps other developers understand and adopt your operator more easily.


### Optimization
All modifications to existing features are categorized as optimization. This can include bug fixes, performance optimization, code structure optimization, documentation optimization, etc. Please confirm that your modification is forward-compatible and will not change the running logic of the code itself. If forward compatibility cannot be guaranteed, please make a special note in the issue.

## How to Contribute
Please follow the ["fork and pull request"](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project) workflow. Here is a short version:  

### Getting Started
1. **Fork the Repository:** Fork the OmAgent repository on GitHub. This creates your own copy where you can make changes.
2. **Clone Your Fork:** Clone your forked repository to your local machine:

   ```bash
   git clone https://github.com/your-username/OmAgent.git
   ```

3. **Create a New Branch:** Create a new branch for your specific contribution:

   ```bash
   git checkout -b your-feature-branch
   ```

### Making Changes

1. **Make Your Changes:** Make your changes to the codebase or documentation.
2. **Commit Your Changes:** Commit your changes with informative commit messages:

   ```bash
   git add .
   git commit -m "Your commit message"
   ```

3. **Push Your Changes:** Push your changes to your forked repository:

   ```bash
   git push origin your-feature-branch
   ```

### Creating a Pull Request

1. **Navigate to Your Fork:** Go to your forked repository on GitHub.
2. **Create a Pull Request:** Click the "New pull request" button.
3. **Select Your Branch:** Select your feature branch as the head and the latest develop branch of the original OmAgent repository as the base.
4. **Add a Description:** Provide a clear description of your changes.
5. **Submit Your Pull Request:** Click the "Create pull request" button.

### Additional Notes

* **Code Style:** Adhere to the project's coding style conventions (PEP 8).
* **Testing:** Ensure your changes don't introduce regressions. Add unit tests if necessary.
* **Communication:** Feel free to discuss your contributions on the project's issue tracker.

### Commands

Here are some useful commands:

* **List branches:** `git branch`
* **Switch to a branch:** `git checkout branch-name`
* **Merge branches:** `git merge other-branch`
* **Pull changes from upstream:** `git pull upstream branch-name`

**Thank you for your contributions!**