use clap::{Args, Parser, Subcommand};

#[derive(Clone, Debug, Parser)]
pub struct OpenvairManagerCli {
    #[command(subcommand)]
    pub command: ManagerCommands,
}

#[derive(Clone, Debug, Args, PartialEq, Eq)]
pub struct OpenvairManagerInstallArgs {
    #[arg(short, long, default_value_t = String::from("aero"))]
    pub user: String,
    #[arg(short, long, default_value_t = String::from("openvair"))]
    pub project_name: String,
    #[arg(short, long, default_value_t = String::from("openvair-docs"))]
    pub docs_project_name: String,
}

#[derive(Clone, Subcommand, Debug, PartialEq, Eq)]
pub enum ManagerCommands {
    Install(OpenvairManagerInstallArgs),
}

#[cfg(test)]
mod tests {

    use clap::Parser;

    use super::*;

    #[test]
    fn test_command_parse() {
        let res = OpenvairManagerCli::parse_from(["openvair-manager", "install", "-u", "test"]);
        assert_eq!(
            res.command,
            ManagerCommands::Install(OpenvairManagerInstallArgs {
                user: String::from("test"),
                project_name: String::from("openvair"),
                docs_project_name: String::from("openvair-docs")
            })
        )
    }
}
