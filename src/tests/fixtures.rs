use std::rc::Rc;

use rstest::fixture;

use crate::{
    cmd_runner::CommandRunner, openvair_manager::python::PythonProvider,
    pkg_management::UbuntuPackageProvider,
};

#[fixture]
pub fn command_runner() -> CommandRunner {
    CommandRunner
}

#[fixture]
pub fn python_provider(command_runner: CommandRunner) -> PythonProvider {
    PythonProvider::new(Rc::new(command_runner))
}

#[fixture]
pub fn ubuntu_package_provider(command_runner: CommandRunner) -> UbuntuPackageProvider {
    UbuntuPackageProvider::new(Rc::new(command_runner))
}
