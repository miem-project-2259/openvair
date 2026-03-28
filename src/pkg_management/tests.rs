#[cfg(feature = "ubuntu")]
use crate::tests::fixtures::command_runner;

use super::*;

#[cfg(feature = "ubuntu")]
#[rstest]
fn test_ubuntu_package_install(command_runner: CommandRunner) {
    let provider = UbuntuPackageProvider::new(&command_runner);

    let res = provider.try_install("hello");
    assert!(
        res.expect("failed to run install").status.success(),
        "process did not terminate successfully"
    );
    assert!(
        provider.check_installed("hello"),
        "failed to find installed hello package"
    );
}
