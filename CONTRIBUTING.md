# Contributing

Welcome and thank you for your interest
in contributing to `one-appconfig`! Before contributing to this
project, please review this document for policies and procedures which
will ease the contribution and review process for everyone. If you have
questions, please contact Vassily Lyutsarev vassilyl@microsoft.com. This project adopted
[Inner Source model](http://aka.ms/innersource).

## Issues and Feature Requests

Issues, bugs and proposed new features should be submitted to our [backlog](https://msrcambridge.visualstudio.com/One/_backlogs/backlog/msrc-appconfig/Issues/). The project uses [Basic process](https://docs.microsoft.com/en-us/azure/devops/boards/get-started/plan-track-work?view=azure-devops&tabs=basic-process) which assumes your input is filed
as an _Issue_. You may also tag the issue with a Bug tag which is optional. Please specify in detail the versions of python and msrc-appconfig package, and a detailed repro for the issue.

## Style Guidelines

The project has adopted [PEP 8](https://www.python.org/dev/peps/pep-0008/) style for code.
We use [flake8](https://pypi.org/project/flake8/) with default options to lint the code.
Additionally, the [pyright](https://github.com/microsoft/pyright) static type checker must run without issues on the code.

## Pull Request Process

1. Prepare your changes in a branch named `<your-alias>/<short-feature-description>`. 
   Alternativly, you may create your personal
   [fork](https://docs.microsoft.com/en-us/azure/devops/repos/git/forks?view=azure-devops) 
   of the repository in Forks project.
1. All new code must come with corresponding [pytest](https://docs.pytest.org/en/latest/) tests. Keep code coverage at 100%.
1. Ensure CI build is successful and tests, including any added or updated tests, pass prior to submitting the pull request.
1. Update any documentation, user and contributor, that is impacted by your changes.
1. Do not change the version number in VERSION.txt.
1. Do not merge your pull request, this is the responsibility of a core developer.

## License Information

The project can be used for Microsoft internal purposes without any limitation.
To use the package outside of Microsoft contact Vassily Lyutsarev vassilyl@microsoft.com.
