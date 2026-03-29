use std::{process::Command, rc::Rc};

use clap::Parser;

use crate::{
    cmd_runner::CommandRunner,
    docker::{installer::UbuntuDockerInstaller, provider::DockerProvider},
    openvair_manager::{
        cli::OpenvairManagerCli,
        files::FilesProvider,
        installer::{config::InstallerConfig, service::OpenvairInstallerService},
        node_exporter::installer::{
            UbuntuNodeExporterInstaller, UbuntuNodeExporterInstallerConfig,
        },
        python::PythonProvider,
        services::SystemdServiceProvider,
    },
    pkg_management::UbuntuPackageProvider,
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
    let files = Rc::new(FilesProvider::new(runner.clone()));
    let pkg = Rc::new(UbuntuPackageProvider::new(runner.clone()));
    let mut docker_installer =
        UbuntuDockerInstaller::new(runner.clone(), files.clone(), pkg.clone());
    let docker = DockerProvider::new(runner.clone());
    let mut python = PythonProvider::new(runner.clone());
    let services = Rc::new(SystemdServiceProvider::new(runner.clone(), files.clone()));

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
            let node_exporter_provider = Rc::new(UbuntuNodeExporterInstaller::new(
                UbuntuNodeExporterInstallerConfig::builder()
                    .proc(&installer_cfg.processor_type)
                    .dependencies_file(&installer_cfg.dependencies_file)
                    .build(),
                runner.clone(),
                files.clone(),
                services.clone(),
            ));

            let mut installer = OpenvairInstallerService::new(
                installer_cfg,
                project_cfg,
                pkg,
                runner,
                files,
                &docker_installer,
                &docker,
                node_exporter_provider,
                &python,
                services,
            );

            installer.install_openvair()?;
        }
    }

    Ok(())
}
