use std::{process::Command, rc::Rc};

use clap::Parser;
use command_macros::cmd;

use crate::{
    cmd_runner::CommandRunner,
    docker::{installer::UbuntuDockerInstaller, provider::DockerProvider},
    openvair_manager::{
        cli::OpenvairManagerCli,
        installer::{config::InstallerConfig, service::OpenvairInstallerService},
        python::PythonProvider,
    },
    pkg_management::{PackageProvider, UbuntuPackageProvider},
    project_config::OpenvairProjectConfig,
};

mod tests;

pub mod cmd_runner;

pub mod pkg_management;

pub mod project_config;

pub mod docker;

pub mod openvair_manager;

fn main() -> anyhow::Result<()> {
    let runner = Rc::new(CommandRunner::new());
    let pkg = Rc::new(UbuntuPackageProvider::new(runner.clone()));
    let mut docker_installer = UbuntuDockerInstaller::new(runner.clone(), pkg.clone());
    let docker = DockerProvider::new(runner.clone());
    let mut python = PythonProvider::new(runner.clone());

    let cli = OpenvairManagerCli::parse();
    match cli.command {
        openvair_manager::cli::ManagerCommands::Install(openvair_manager_install_args) => {
            let installer_cfg =
                InstallerConfig::builder().build(runner.clone(), &openvair_manager_install_args);
            let project_cfg =
                OpenvairProjectConfig::try_from_file(&installer_cfg.project_config_file)?;

            let os_type = runner
                .pipe(
                    Command::new("lsb_release").arg("-i"),
                    Command::new("cut").args(["-f", "2-"]),
                )
                .output
                .to_lowercase();
            docker_installer.set_os_type(&os_type);
            docker_installer.set_proc(&installer_cfg.processor_type);
            python.set_python_path(&format!("{}/venv/bin/python3", installer_cfg.project_path));

            let mut installer = OpenvairInstallerService::new(
                installer_cfg,
                project_cfg,
                pkg,
                &runner,
                &docker_installer,
                &docker,
                &python,
            );

            installer.install_openvair()?;
        }
    }

    Ok(())
}
