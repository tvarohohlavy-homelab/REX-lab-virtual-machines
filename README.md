# lab-virtual-machines
LAB VMs build in VMware vCenter


## Prerequisites:
- VMware vSphere Host with vCenter managing it
- Self-hosted Github Runner tagged [self-hosted, linux, initial] allowed for this repository
- All necessary variables and secrets set at repository or organization level
- VM templates pre-created with workflows from [LAB-PACKER repo](https://github.com/Rexonix-Infra/lab-packer)
- Necessary files available in vCenter Content Library

## Usage:
### 1. LAB DNS
> **IMPORTANT: this workflow is to be run once**

Run workflow at [Create pihole01/02 VMs](https://github.com/Rexonix-Infra/lab-virtual-machines/actions/workflows/create-pihole01-02-vms.yml)

Create two Pihole VMs with keepalived between them serving DNS records from: [custom.list.tsv](https://github.com/Rexonix-Infra/lab-virtual-machines/blob/main/pihole/etc/pihole/custom.list.tsv)

Subsequent editing of the TSV file will sync it on both VMs with the version in this Repository using automatically triggered workflow [here](https://github.com/Rexonix-Infra/lab-virtual-machines/actions/workflows/update-pihole-custom-list.yml)

### 2. Jumphost
> **IMPORTANT: this workflow is to be run once**

Run workflow at [Create jumphost01 VM](https://github.com/Rexonix-Infra/lab-virtual-machines/actions/workflows/create-jumphost01-vm.yml)

Creates jumphost VM using above DNS

### 9. Cisco Modelling LABs
> **IMPORTANT: this workflow is to be run once**

Run workflow at [Create cml VM](https://github.com/Rexonix-Infra/lab-virtual-machines/actions/workflows/create-cml-vm.yml)

Create Cisco CML VM fully preconfigured and with registered license
