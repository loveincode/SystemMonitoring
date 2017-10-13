#coding=utf-8
#————————————————————————————————————————————
#    程序：python web 实现 系统监控 API
#    作者：hyf
#    日期：2017.10.12
#————————————————————————————————————————————

#Flask web框架  jsonify json格式处理 abort终止异常处理  make_response 回应 request 请求 
from flask import Flask,jsonify,abort,make_response,request

import psutil
#os
import platform
from collections import OrderedDict
#net
import netifaces
#cors 跨域访问
from flask_cors import *

#日志
import logging
import logging.handlers

app = Flask(__name__);
CORS(app, supports_credentials=True);

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s [%(lineno)d] - %(message)s')

file_handler = logging.FileHandler('psutil.log')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

@app.route('/system/info', methods=['GET'])
def get_systeminfo():
    app.logger.info('enter get_systeminfo');
    
    #操作系统名称及版本号
    systemversion = platform.platform()
	
    #获取操作系统的位数
    architecture = platform.architecture()
	
    #操作系统类型
    system = platform.system()
	
    systeminfo ={
        'systemversion 操作系统名称及版本号': systemversion,
        'system 操作系统':system,
        'architecture 位数':architecture[0]
    }
    return jsonify({'systeminfo': systeminfo});

@app.route('/system/cpu', methods=['GET'])
def get_cpu():
    app.logger.info('enter get_cpu');
    CPUinfo=OrderedDict()
    procinfo=OrderedDict()
    nprocs = 0
    with open('/proc/cpuinfo') as f:
        for line in f:
            if not line.strip():
                #end of one processor
                CPUinfo['proc%s' % nprocs]=procinfo
                nprocs = nprocs+1
                #Reset
                procinfo=OrderedDict()
            else:
                if len(line.split(':')) == 2:
                    procinfo[line.split(':')[0].strip()] = line.split(':')[1].strip()
                else:
                    procinfo[line.split(':')[0].strip()] = ''
	
    #/proc/cpuinfo
    #vendor_id	: GenuineIntel
    #model name	: Intel(R) Xeon(R) CPU E5-2620 v2 @ 2.10GHz
    #cpu MHz		: 2094.952
    
    psutil.cpu_times()

    #获取cpu逻辑个数
    count = psutil.cpu_count()
    #cpu综合使用率
    percent = psutil.cpu_percent() 
    cpu ={
	    'vendor_id 厂商':CPUinfo['proc0']['vendor_id'],
		'model name 名称':CPUinfo['proc0']['model name'],
		'cpu MHz 频率':CPUinfo['proc0']['cpu MHz'],
        'count 核数': count,
        'percent 使用率(%)':percent
    }
    return jsonify({'cpu': cpu});

@app.route('/system/memory', methods=['GET'])
def get_memory():
    app.logger.info('enter get_memory');
    
    psutil.virtual_memory();
    #都是以byte单位输出
    #total=17254203392, available=12436979712, percent=27.899999999999999, used=4557484032, free=4773912576, 
    #active=8057135104, inactive=2576429056, buffers=542326784, cached=7380480000, shared=204800)
	
    #total: 内存的总大小.
    total = psutil.virtual_memory().total;
    #available: 可以用来的分配的内存，不同系统计算方式不同； Linux下的计算公式:free+ buffers +　cached
    available = psutil.virtual_memory().available;	
    #percent: 已经用掉内存的百分比 (total - available) / total 100.
    percent = psutil.virtual_memory().percent;
    #used: 已经用掉内存大小，不同系统计算方式不同
    used = psutil.virtual_memory().used;
    #*free: 空闲未被分配的内存，Linux下不包括buffers和cached
    free = psutil.virtual_memory().free;
    #active: (UNIX): 最近使用内存和正在使用内存。
    active = psutil.virtual_memory().active;
    #inactive: (UNIX): 已经分配但是没有使用的内存
    inactive = psutil.virtual_memory().inactive;
    #buffers: (Linux, BSD): 缓存，linux下的Buffers
    buffers = psutil.virtual_memory().buffers;
    #cached:(Linux, BSD): 缓存，Linux下的cached.
    cached = psutil.virtual_memory().cached;
    #shared: (BSD): 缓存
    shared = psutil.virtual_memory().shared;
	
    memory ={
	    'total 总内存 byte': total,
	    'percent 使用率 %': percent, 
        'used 已使用 byte': used,
        'free 未分配 byte':free
	}
    print "total: %.2f(M)" % (float(total)/1024/1024/1024);
    return jsonify({'memory': memory});
	
@app.route('/system/disk', methods=['GET'])
def get_disk():
    app.logger.info('enter get_disk');
	
    disks = [];
    psutil.disk_partitions();
    #[sdiskpart(device='/dev/sda1', mountpoint='/', fstype='ext4', opts='rw'), 
	#sdiskpart(device='/dev/sda2', mountpoint='/opt', fstype='ext4', opts='rw'), 
	#sdiskpart(device='/dev/sda8', mountpoint='/tmp', fstype='ext4', opts='rw'), 
	#sdiskpart(device='/dev/sda6', mountpoint='/var/lib', fstype='ext4', opts='rw'), 
	#sdiskpart(device='/dev/sda5', mountpoint='/var/lib/mysql', fstype='ext4', opts='rw'), 
	#sdiskpart(device='/dev/sda7', mountpoint='/var/log', fstype='ext4', opts='rw')]
	
    length = len(psutil.disk_partitions());
    for i in range(length):
        print psutil.disk_partitions()[i]
        disk = {
            'name 分区名':psutil.disk_partitions()[i].device,
            'total 总大小 G':psutil.disk_usage(psutil.disk_partitions()[i].mountpoint).total/1024/1024/1024.0,
			'used 已使用 G':psutil.disk_usage(psutil.disk_partitions()[i].mountpoint).used/1024/1024/1024.0,
			'free 空闲 G':psutil.disk_usage(psutil.disk_partitions()[i].mountpoint).free/1024/1024/1024.0,
			'percent 使用率 %':psutil.disk_usage(psutil.disk_partitions()[i].mountpoint).percent,
			'path 挂载路径':psutil.disk_partitions()[i].mountpoint,
			'fstype 分区格式':psutil.disk_partitions()[i].fstype
        }
        disks.append(disk)	
    return jsonify({'disks': disks});
	
	
@app.route('/system/network', methods=['GET'])
def get_network():
    app.logger.info('enter get_network');
	
    routingGateway=netifaces.gateways()['default'][netifaces.AF_INET][0] 
    routingNicName=netifaces.gateways()['default'][netifaces.AF_INET][1] #eth0
    routingNicMacAddr = netifaces.ifaddresses(routingNicName)[netifaces.AF_LINK][0]['addr']
    routingIPAddr =netifaces.ifaddresses(routingNicName)[netifaces.AF_INET][0]['addr']
    routingIPNetmask=netifaces.ifaddresses(routingNicName)[netifaces.AF_INET][0]['netmask']
	
	#获取网卡多个ip
	#psutil.net_io_counters(pernic=True)[routingNicName]
	
	#['lo0', 'gif0', 'stf0', 'en0', 'en1', 'fw0']
    networks=[];
    length = len(netifaces.interfaces());
    for i in range(length):
        Nicname = netifaces.interfaces()[i];
		
        Gateway = "";
        MacAddr = "";
        IpAddr = "";
        IPNetmask="";
        #bytes_sent=0;
        #bytes_recv=0;
        #packets_sent=0;
        #packets_recv=0;
		
        try:
            if ":" not in Nicname:
                MacAddr = netifaces.ifaddresses(Nicname)[netifaces.AF_LINK][0]['addr'];
            
            IpAddr = netifaces.ifaddresses(Nicname)[netifaces.AF_INET][0]['addr'];
            IPNetmask=netifaces.ifaddresses(routingNicName)[netifaces.AF_INET][0]['netmask'];
			
            if "lo" in Nicname:
                Gateway = netifaces.ifaddresses(Nicname)[netifaces.AF_INET][0]['peer'];
            else:
                Gateway = netifaces.ifaddresses(Nicname)[netifaces.AF_INET][0]['broadcast'];
			
            #if ":" not in Nicname:
            #    bytes_sent = psutil.net_io_counters(pernic=True)[Nicname].bytes_sent,
            #    bytes_recv = psutil.net_io_counters(pernic=True)[Nicname].bytes_recv,
            #    packets_sent = psutil.net_io_counters(pernic=True)[Nicname].packets_sent,
            #    packets_recv = psutil.net_io_counters(pernic=True)[Nicname].packets_recv,
			
            
        except KeyError:
            pass
        
        if ":" in Nicname:
            network = {
                'Nicname 网卡名称':Nicname,
                'Gateway 网关':Gateway,
                'ip地址':IpAddr,
                'Netmask 网络掩码':IPNetmask,
		    }
        else:
            network = {
                'Nicname 网卡名称':Nicname,
                'Gateway 网关':Gateway,
                'NIcMacAddr 网卡mac地址':MacAddr,
                'ip地址':IpAddr,
                'Netmask 网络掩码':IPNetmask,	
                'bytes_sent 发送字节数': psutil.net_io_counters(pernic=True)[Nicname].bytes_sent,
                'bytes_recv 接收字节数': psutil.net_io_counters(pernic=True)[Nicname].bytes_recv,
                'packets_sent 发送包个数': psutil.net_io_counters(pernic=True)[Nicname].packets_sent,
                'packets_recv 接收包个数': psutil.net_io_counters(pernic=True)[Nicname].packets_recv,
		    }
        networks.append(network)	
    return jsonify({'networks': networks});
	
    #networks={
    #    'Nicname 网卡名称':routingNicName,
    #    'Gateway 网关':routingGateway,
    #    'NIcMacAddr 网卡mac地址':routingNicMacAddr,
    #    'ip地址':routingIPAddr,
    #    'Netmask 网络掩码':routingIPNetmask,	
    #    'bytes_sent 发送字节数': psutil.net_io_counters(pernic=True)[routingNicName].bytes_sent,
	#	'bytes_recv 接收字节数': psutil.net_io_counters(pernic=True)[routingNicName].bytes_recv,
	#	'packets_sent 发送包个数': psutil.net_io_counters(pernic=True)[routingNicName].packets_sent,
	#	'packets_recv 接收包个数': psutil.net_io_counters(pernic=True)[routingNicName].packets_recv,
	#	'errout 发送数据包错误总数': psutil.net_io_counters(pernic=True)[routingNicName].errout,
	#	'dropin 接收时丢弃的数据包的总数': psutil.net_io_counters(pernic=True)[routingNicName].dropin,
    #};	
    
	
@app.route('/system/process', methods=['GET'])
def get_process():
    app.logger.info('enter get_process');
	
@app.route('/system/user', methods=['GET'])
def get_user():
    app.logger.info('enter get_user');

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Request Error'}), 400)

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5001,debug=True)
