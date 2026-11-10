#!/usr/bin/env bash
set -euo pipefail

slurm_dir="$(cd "$(dirname "$0")" && pwd)"
host="$(hostname)"

export DEBIAN_FRONTEND=noninteractive
apt-get install -y -qq slurm-wlm munge

node_line="$(slurmd -C | head -n 1 | sed -E 's/ UpTime=.*//')"

install -d -o slurm -g slurm /var/spool/slurmctld /var/spool/slurmd /var/log/slurm

sed -e "s|@HOSTNAME@|${host}|g" -e "s|@NODE_LINE@|${node_line}|" \
    "${slurm_dir}/slurm.conf.template" > /etc/slurm/slurm.conf
sed -e "s|@HOSTNAME@|${host}|g" \
    "${slurm_dir}/gres.conf.template" > /etc/slurm/gres.conf

systemctl enable --now munge
systemctl restart slurmctld slurmd
systemctl enable slurmctld slurmd
sinfo --Node --long
