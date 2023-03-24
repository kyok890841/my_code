import os, glob, sys, re
import datetime
import pprint



class PowerConsumption():
    def __init__(self):
        #self.root_dir = os.environ["SMC_ROOT_DIR"]
        self.root_dir = "/opt_shared/smci/kapl/production/"
        self.data_dir = f'{self.root_dir}/data/'
        self.reports_dir = f'{self.root_dir}/reports/'
        self.config_dir = f'{self.root_dir}/config/'

    def SourceConfig():
        with open("../../system-config.txt", "r") as f:
            rcfg = f.read().split("\n")
        rcfg.pop()
        for idx, line in enumerate(rcfg):
            if "#" not in line:
                os.environ[f"{line.split('=')[0]}"] = f"{line.split('=')[1]}"

    def getNodeInfo(self, nodename):
        with open(f"{self.config_dir}cluster-node-info.txt", "r") as f:
            node_read = f.read().split("\n")
        for idx, line in enumerate(node_read):
            if nodename in line:
                return line.split()[0:2]
    def summary(self):
        data = {}
        default = {'time':'', 
            'sn':0, 'ln':0, 'an':0, 'cn':0,
            'll12':0, 'll23':0,'ll31':0,
            'rr12':0, 'rr23':0,'rr31':0,
            'lr12':0, 'lr23':0,'lr31':0,
            'rl12':0, 'rl23':0,'rl31':0,
            'pdu12':0, 'pdu23':0, 'pdu31':0,
            'all_w':0,
            'snmp_miss':'', 'ipmi_miss':''}
        data = {x:default.copy() for x in range(1,20)}
        data.update({x:default.copy() for x in ['BD1', 'BD2', 'BD3', 'BD4', 'BD5', 'SYS']})

        bd_num = 1
        for rack_num in range(1,20):
            if rack_num in [5,9,12,16]:
                bd_num += 1
            ipmi_txt = glob.glob(f"{self.data_dir}power-temp/*r{rack_num}[!0-9]*.txt")
            snmp_txt = glob.glob(f"{self.data_dir}smart-pdu/*r{rack_num}[!0-9]*.txt")

            # add snmp_w
            for txt in snmp_txt:
                pdu_type = txt.split("/")[-1].split("_")[1].split("-")[1]
                node_name = txt.split("/")[-1].split("_")[0]
                if pdu_type == 'l':
                    pdu_type += 'l'
                elif pdu_type == 'r':
                    pdu_type += 'r'
                read = open(txt, 'r').read().split("\n")
                read.pop()
                last_split = read[-1].split()
                #if last_split[0] != "hpl-power":
                #    sys.exit(0)
                if read:
                    time = last_split[3]
                if time:
                    for key in data.keys():
                        data[key]['time'] = time
                if len(last_split) > 4:
                    data[rack_num][f'{pdu_type}12'] += int(last_split[4])
                    data[rack_num]['pdu12'] += int(last_split[4])
                    data[rack_num]['all_w'] += int(last_split[4])
                    data[f'BD{bd_num}'][f'{pdu_type}12'] += int(last_split[4])
                    data[f'BD{bd_num}']['pdu12'] += int(last_split[4])
                    data[f'BD{bd_num}']['all_w'] += int(last_split[4])
                    data['SYS'][f'{pdu_type}12'] += int(last_split[4])
                    data['SYS']['pdu12'] += int(last_split[4])
                    data['SYS']['all_w'] += int(last_split[4])
                    data[rack_num][f'{pdu_type}23'] += int(last_split[5])
                    data[rack_num]['pdu23'] += int(last_split[5])
                    data[rack_num]['all_w'] += int(last_split[5])
                    data[f'BD{bd_num}'][f'{pdu_type}23'] += int(last_split[5])
                    data[f'BD{bd_num}']['pdu23'] += int(last_split[5])
                    data[f'BD{bd_num}']['all_w'] += int(last_split[5])
                    data['SYS'][f'{pdu_type}23'] += int(last_split[5])
                    data['SYS']['pdu23'] += int(last_split[5])
                    data['SYS']['all_w'] += int(last_split[5])
                    data[rack_num][f'{pdu_type}31'] += int(last_split[6])
                    data[rack_num]['pdu31'] += int(last_split[6])
                    data[rack_num]['all_w'] += int(last_split[6])
                    data[f'BD{bd_num}'][f'{pdu_type}31'] += int(last_split[6])
                    data[f'BD{bd_num}']['pdu31'] += int(last_split[6])
                    data[f'BD{bd_num}']['all_w'] += int(last_split[6])
                    data['SYS'][f'{pdu_type}31'] += int(last_split[6])
                    data['SYS']['pdu31'] += int(last_split[6])
                    data['SYS']['all_w'] += int(last_split[6])
                else:
                    data[rack_num]['snmp_miss'] += f" {node_name}"
                    print(f"{txt} don't have snmp data at {data[key]['time']}")

            # add ipmi_w
            for txt in ipmi_txt:
                #print(txt)
                node_name = txt.split('/')[-1].split('_')[0]
                location, node_type = self.getNodeInfo(node_name)
                
                read = open(txt, 'r').read().split("\n")
                read2 = open(txt, 'r').read()
                match = re.findall(f"{data[rack_num]['time']}\s+(\d+)", read2)
                if match:
                    watt = int(match[0])
                    data[rack_num][node_type] += watt
                    data[f'BD{bd_num}'][node_type] += watt
                    data['SYS'][node_type] += watt
                else:
                    data[rack_num]['ipmi_miss'] += f" {node_name}"
            for key, val in data[rack_num].items():
                     if val == 0:
                        data[rack_num][key] = 'NA'
            if rack_num in [4, 8, 11, 15, 19]:
                for key, val in data[f'BD{bd_num}'].items():
                    if val == 0:
                        data[f'BD{bd_num}'][key] = 'NA'
        for key, val in data['SYS'].items():
            if val == 0:
                data['SYS'][key] = 'NA'

        #write
        output = f'{self.reports_dir}power-consumption.txt'
        if not os.path.isfile(output):
            with open(output, 'w+') as w:
                w.write(f"##! Title: Power consumption\n")
                w.write("##! Priority: 1\n")
                w.write("##! TimeStamp: NA\n")
                w.write("##! Status: NA\n")
                w.write("##! Summary: NA\n")
                w.write("rack tstamp    sn-ln-an-cn_w           ll-12/23/31_w     rr-12/23/31_w     lr-12/23/31_w     rl-12/23/31_w     pdu-12-23-31      All_w  Note\n")
                w.write("---- --------- ----------------------- ----------------- ----------------- ----------------- ----------------- ----------------- ------ --------\n")
        with open(output, 'a+') as w:
            for key, val in data.items():
                if key == 1:
                    w.write("rack tstamp    sn-ln-an-cn_w           ll-12/23/31_w     rr-12/23/31_w     lr-12/23/31_w     rl-12/23/31_w     pdu-12-23-31      All_w  Note\n")
                    w.write("---- --------- ----------------------- ----------------- ----------------- ----------------- ----------------- ----------------- ------ --------\n")
                if key in range(1,20):
                    w.write(f"r{key}"+" "*(4-len(str(key))-1+1))
                else:
                    w.write(f"{key}"+" "*(4-len(str(key))+1))
                w.write(f"{val['time']} ")
                type_str = f"{val['sn']}-{val['ln']}-{val['an']}-{val['cn']}"
                w.write(type_str+" "*(23-len(type_str)+1))
                ll_str = f"{val['ll12']}/{val['ll23']}/{val['ll31']}"
                w.write(ll_str+" "*(17-len(ll_str)+1))
                rr_str = f"{val['rr12']}/{val['rr23']}/{val['rr31']}"
                w.write(rr_str+" "*(17-len(rr_str)+1))
                lr_str = f"{val['lr12']}/{val['lr23']}/{val['lr31']}"
                w.write(lr_str+" "*(17-len(lr_str)+1))
                rl_str = f"{val['rl12']}/{val['rl23']}/{val['rl31']}"
                w.write(rl_str+" "*(17-len(rl_str)+1))
                pdu_str = f"{val['pdu12']}/{val['pdu23']}/{val['pdu31']}"
                w.write(pdu_str+" "*(17-len(pdu_str)+1))
                w.write(f"{val['all_w']}"+" "*(6-len(str(val['all_w']))-1))
                if val['snmp_miss'] != '' and val['ipmi_miss'] == '':
                    w.write(f"{val['snmp_miss']} no snmp data\n")
                elif val['ipmi_miss'] != '' and val['snmp_miss'] == '':
                    w.write(f" {val['ipmi_miss']} no ipmi data\n")
                elif val['snmp_miss'] != '' and val['ipmi_miss'] != '':
                    w.write(f"{val['snmp_miss']} no snmp data, and {val['ipmi_miss']} no impi data\n")
                else:
                    w.write("\n")
                if key == 10:
                    w.write(f"r{key}  {val['time']} NA-NA-4800-NA           NA/NA/NA          NA/NA/NA          NA/NA/NA          NA/NA/NA          NA/NA/NA          4800\n")
            w.write("\n")
if __name__ == '__main__':
    #SourceConfig()
    pc = PowerConsumption()
    pc.summary()
