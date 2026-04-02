use crate::openvair_manager::cmd_runner::{CommandResult, CommandRunner};
use std::{process::Command, rc::Rc};

pub trait PackageProvider {
    fn try_check_installed(&self, package_name: &str) -> anyhow::Result<bool>;
    fn try_install(&self, package_name: &str) -> anyhow::Result<CommandResult>;
    fn check_installed(&self, package_name: &str) -> bool {
        self.try_check_installed(package_name)
            .expect(&format!("failed to check if {package_name} is installed"))
    }
    fn install(&self, package_name: &str) -> CommandResult {
        self.try_install(package_name)
            .expect(&format!("failed to install {package_name}"))
    }
}

#[derive(Clone, Debug)]
pub struct UbuntuPackageProvider {
    runner: Rc<CommandRunner>,
}

impl UbuntuPackageProvider {
    pub fn new(runner: Rc<CommandRunner>) -> Self {
        UbuntuPackageProvider { runner }
    }
}

impl PackageProvider for UbuntuPackageProvider {
    fn try_check_installed(&self, package_name: &str) -> anyhow::Result<bool> {
        let mut dpkg_cmd = Command::new("dpkg");
        let mut grep_cmd = Command::new("grep");

        let res = self
            .runner
            .try_pipe(dpkg_cmd.arg("-l"), grep_cmd.args(["-q", package_name]))?;

        return Ok(res.status.success());
    }

    fn try_install(&self, package_name: &str) -> anyhow::Result<CommandResult> {
        let mut sudo_cmd = Command::new("sudo");

        let res = self
            .runner
            .try_run(sudo_cmd.args(["apt-get", "install", "-y", package_name]))?;
        Ok(res)
    }
}

#[cfg(test)]
mod tests;
