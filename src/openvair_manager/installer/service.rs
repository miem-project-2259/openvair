use std::{fs::File, process::Command, thread, time::Duration};

use log::info;
use serde_valid::Validate;

use crate::{
    cmd_runner::CommandRunner,
    docker::{
        installer::DockerInstaller,
        provider::{DockerProvider, DockerRunConfig},
    },
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
        python: &'a PythonProvider<'a>,
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
            python,
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

        self.set_repo_owner()?;
        self.docker_installer.install_docker()?;
        self.setup_postgres_container()?;
        self.setup_rabbitmq_container()?;

        self.setup_snmp()?;
        self.make_migrations()?;
        self.generate_certificate()?;
        self.setup_novnc()?;

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
            "open-iscsi",
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

    fn set_repo_owner(&self) -> anyhow::Result<()> {
        info!("changing owner of the repo");
        self.runner.try_run(Command::new("sudo").args([
            "chown",
            "-R",
            &format!(
                "{}:{}",
                self.installer_config.user, self.installer_config.user
            ),
            &self.installer_config.project_path,
        ]))?;
        Ok(())
    }

    fn setup_postgres_container(&self) -> anyhow::Result<()> {
        info!("creating postgresql docker container");
        const PG_CONTAINER_NAME: &str = "postgres";
        const PG_DB_NAME: &str = "openvair";

        let pg_run = DockerRunConfig::new("postgres -c 'listen_addresses=*'")
            .builder()
            .name(PG_CONTAINER_NAME)
            .restart("unless-stopped")
            .env(&[
                format!("POSTGRES_USER={}", self.installer_config.user).as_str(),
                format!("POSTGRES_PASSWORD={}", self.installer_config.user).as_str(),
            ])
            .ports(&format!(
                "{}:{}",
                self.project_config.database.port, self.project_config.database.port
            ))
            .detach(true)
            .build();

        self.docker.try_run(&pg_run)?;
        thread::sleep(Duration::from_secs(5));

        // Create DB
        self.docker.try_exec(
            PG_CONTAINER_NAME,
            &format!(
                "psql -U {} -c 'CREATE DATABASE {};'",
                self.installer_config.user, PG_DB_NAME
            ),
        )?;

        // Setup Permissions
        self.docker.try_exec(
            PG_CONTAINER_NAME,
            &format!(
                "psql -U {} -c 'GRANT ALL PRIVILEGES ON DATABASE {} TO {};'",
                self.installer_config.user, PG_DB_NAME, self.installer_config.user,
            ),
        )?;

        Ok(())
    }

    fn setup_rabbitmq_container(&self) -> anyhow::Result<()> {
        let rabbitmq_user = self.project_config.rabbitmq.user.as_str();
        let rabbitmq_password = self.project_config.rabbitmq.password.as_str();
        let rabbitmq_host = match self.project_config.rabbitmq.host.as_str() {
            "localhost" => "127.0.0.1",
            addr => addr,
        };
        let rabbitmq_port = self.project_config.rabbitmq.port;

        // TODO this should prooooobably be moved to be a configurable version
        //
        // But for now "it just needs to be"
        let hostname = self.runner.try_run(&mut Command::new("hostname"))?.output;
        let run_cfg = DockerRunConfig::new("rabbitmq:3.11")
            .builder()
            .detach(true)
            .hostname(&hostname)
            .name("rabbit")
            .env(&[
                &format!("RABBITMQ_DEFAULT_USER={rabbitmq_user}"),
                &format!("RABBITMQ_DEFAULT_PASS={rabbitmq_password}"),
            ])
            .ports(&format!("{rabbitmq_host}:{rabbitmq_port}:{rabbitmq_port}"))
            .restart("unless-stopped")
            .build();

        self.docker.try_run(&run_cfg)?;

        Ok(())
    }

    fn setup_snmp(&self) -> anyhow::Result<()> {
        let pkgs = ["snmp", "snmpd"];

        for p in pkgs {
            self.pkg.try_install(p)?;
        }

        info!("appending snmp config");
        const SNMPD_CONF: &str = "/etc/snmp/snmpd.conf";
        if !std::fs::exists(SNMPD_CONF)? {
            anyhow::bail!("{} file does not exist", SNMPD_CONF);
        }

        self.runner.try_pipe(
            Command::new("echo").arg("view systemonly  included    .1.3.6.1.4.1.54641"),
            Command::new("sudo").args(["tee", "-a", SNMPD_CONF]),
        )?;
        self.runner.try_pipe(
            Command::new("echo").arg("rocommunity public default -V systemonly"),
            Command::new("sudo").args(["tee", "-a", SNMPD_CONF]),
        )?;
        info!("successfullyu added lines to {}", SNMPD_CONF);

        Ok(())
    }

    fn make_migrations(&self) -> anyhow::Result<()> {
        info!("running alembic migrations");
        self.runner.try_run(
            Command::new("sudo")
                .args([
                    &format!("{}/venv/bin/python3", self.installer_config.project_path),
                    "-m",
                    "alembic",
                    "-c",
                    &format!("{}/alembic.ini", self.installer_config.project_path),
                    "upgrade",
                    "head",
                ])
                .current_dir(&self.installer_config.project_path),
        )?;

        Ok(())
    }

    fn generate_certificate(&self) -> anyhow::Result<()> {
        const CERT_DURATION_DAYS: u32 = 36500;
        let KEY_FILE: &str = &format!("{}/key.pem", self.installer_config.project_path);
        let CERT_FILE: &str = &format!("{}/cert.pem", self.installer_config.project_path);
        let CONFIG_FILE: &str = &format!("{}/openssl.cnf", self.installer_config.project_path);

        if !std::fs::exists(CONFIG_FILE)? {
            anyhow::bail!("configuration file {} not found", CONFIG_FILE);
        }

        info!("configuration file {} found", CONFIG_FILE);

        self.runner.try_run(Command::new("openssl").args([
            "req",
            "-x509",
            "-newkey",
            "rsa:4096",
            "-keyout",
            KEY_FILE,
            "-out",
            CERT_FILE,
            "-days",
            &CERT_DURATION_DAYS.to_string(),
            "-nodes",
            "-config",
            CONFIG_FILE,
        ]))?;
        Ok(())
    }

    fn setup_novnc(&self) -> anyhow::Result<()> {
        self.runner.try_run(Command::new("git").args([
            "clone",
            "https://github.com/novnc/noVNC.git",
            &format!(
                "{}/{}/libs/noVNC",
                self.installer_config.project_path, self.installer_config.project_name
            ),
        ]))?;

        Ok(())
    }

    fn save_project_config(&self) -> anyhow::Result<()> {
        self.project_config
            .try_save_file(&self.installer_config.project_config_file)?;
        Ok(())
    }
}
