use std::{process::Command, rc::Rc};

use super::PackageProvider;
use crate::openvair_manager::cmd_runner::{CommandResult, CommandRunner};

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
