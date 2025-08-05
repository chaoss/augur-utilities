 podman-compose down --remove-orphans && podman container prune -f && sudo systemctl reset-failed && sudo find /run/systemd/transient /etc/systemd/system -name 'podman-*.timer' -delete
