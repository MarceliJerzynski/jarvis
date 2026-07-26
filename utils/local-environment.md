# Local Environment & Network Troubleshooting

- **VPN / Connection Failures (git fetch/pull, etc.):**
  If network operations fail with host-resolution or access errors (such as `Could not resolve host: git.psi-mt.de` when running `git fetch` on `sp-prod`), it is 95% likely that the VPN connection on the host machine has disconnected.
  - When this error occurs, explicitly inform the user that the host's VPN connection has probably disconnected.
