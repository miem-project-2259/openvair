use std::process::Command;

use log::info;
use serde_valid::Validate;

use crate::{
    cmd_runner::CommandRunner,
    docker::{installer::DockerInstaller, provider::DockerProvider},
    openvair_manager::{installer::config::InstallerConfig, python::PythonProvider},
    pkg_management::PackageProvider,
    project_config::OpenvairProjectConfig,
};

pub struct OpenvairInstallerService<'a> {
    installer_config: InstallerConfig,
    project_config: OpenvairProjectConfig,
    pkg: &'a dyn PackageProvider,
    runner: &'a CommandRunner,
    docker_installer: &'a dyn DockerInstaller,
    docker: &'a DockerProvider<'a>,
    python: &'a PythonProvider<'a>,
}

impl<'a> OpenvairInstallerService<'a> {
    pub fn new(
        installer_config: InstallerConfig,
        pkg: &'a dyn PackageProvider,
        runner: &'a CommandRunner,
        docker_installer: &'a dyn DockerInstaller,
        docker: &'a DockerProvider<'a>,
    ) -> Self {
        let config_path = installer_config.project_config_file.clone();
        Self {
            installer_config,
            project_config: OpenvairProjectConfig::try_from_file(&config_path)
                .expect("failed to read config file"),
            pkg,
            runner,
            docker_installer,
            docker,
        }
    }

    pub fn install_openvair(&mut self) -> anyhow::Result<()> {
        info!("starting openvair installation");

        self.project_config.validate()?;
        self.create_jwt_secret()?;
        self.get_os_type()?;

        self.prepare_system_packages()?;
        self.make_and_configure_venv()?;
        self.prepare_python_packages()?;

        todo!()
    }

    fn create_jwt_secret(&mut self) -> anyhow::Result<()> {
        info!("creating jwt secret");
        let secret = self
            .runner
            .run(Command::new("openssl").args(["rand", "-hex", "32"]))
            .output;
        self.project_config.jwt.secret = Some(secret.to_string());
        self.save_project_config()?;

        info!("jwt secret created successfully");
        Ok(())
    }

    fn get_os_type(&mut self) -> anyhow::Result<()> {
        info!("reading os type");
        let os_type = self
            .runner
            .pipe(
                Command::new("lsb_release").arg("-i"),
                Command::new("cut").args(["-f", "2-"]),
            )
            .output
            .to_lowercase();

        info!("got os type: {}", &os_type);
        self.project_config.os_data.os_type = os_type;
        self.save_project_config()?;
        Ok(())
    }

    fn prepare_system_packages(&self) -> anyhow::Result<()> {
        let pkgs = [
            // Python things
            "python3-venv",
            "python3-pip",
            "libpq-dev",
            "python3-websockify",
            // Libvirt requirements
            "qemu-kvm",
            "libvirt-daemon-system",
            "libvirt-clients",
            "bridge-utils",
            "libvirt-dev",
            "python3-dev",
            "build-essential",
            // Storage things
            "nfs-common",
            "xfsprogs",
            // ---
            "openvswitch-switch",
            "multipath-tools",
        ];

        for p in pkgs {
            self.pkg.try_install(p)?;
        }

        Ok(())
    }

    fn make_and_configure_venv(&self) -> anyhow::Result<()> {
        info!("making venv");
        self.runner.try_run(
            Command::new("python3")
                .args([
                    "-m",
                    "venv",
                    &format!("{}/venv", self.installer_config.project_path),
                ])
                .current_dir(&self.installer_config.project_path),
        )?;

        info!("exporting pythonpath");
        self.runner.try_pipe(
            Command::new("echo").arg(format!(
                "'export PYTHONPATH={}:",
                &self.installer_config.project_path
            )),
            Command::new("sudo").args([
                "tee",
                "-a",
                &format!("{}/venv/bin/activate", &self.installer_config.project_path),
            ]),
        )?;
        Ok(())
    }

    fn prepare_python_packages(&self) -> anyhow::Result<()> {
        info!("installing misc python packages");
        let python_pkgs = ["libvirt-python", "wheel"];
        for p in python_pkgs {
            self.python.install(p);
        }

        info!("installing requirements");
        self.python.install_requirements(&format!(
            "{}/requirements.txt",
            self.installer_config.project_path
        ));
        info!("install precommit");
        self.runner.try_run(
            Command::new(format!(
                "{}/venv/bin/pre-commit",
                self.installer_config.project_path
            ))
            .arg("install"),
        )?;
        Ok(())
    }

    fn save_project_config(&self) -> anyhow::Result<()> {
        self.project_config
            .try_save_file(&self.installer_config.project_config_file)?;
        Ok(())
    }
}
