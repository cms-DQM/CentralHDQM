#this file is used to produce the .ini files and the map used in hcal_metrics.py also the display.js
#you can copy paste the content of these files to the correct place

hcal_map_rbx_epd = {
'':[]
}
hcal_map = {
'':[]
}
RBX_name_rbx = ['HBP', 'HBM', 'HEP', 'HEM', 'HFP', 'HFM', 'HOM', 'HOP']
RBX_name_depth = ['HBP', 'HBM', 'HEP', 'HEM', 'HFP', 'HFM', 'HO0', 'HO1', 'HO2']

#for DigiTming
#{0} is the name of RBX
template_ini_DIGITiming_RBX="""
[plot:DIGITiming-MeanTime-{0}]
metric = basic.Mean()
relativePath = Hcal/DigiTask/TimingCut/SubdetPM/{0}
yTitle = Mean of Timing - {0} [TS]
"""
#{0} is the name of RBX
#{1} is the depth name
#{2} is the vector of depth
#{3} is the first depth
#{4} is the second depth
#{5} is the third depth
template_ini_DIGITiming_2Ddepth="""
[plot:DIGITiming-MeanTime-{0}-depth{1}]
metric = hcal_metrics.RBXMean('{0}',{2})
relativePath = Hcal/DigiTask/DigiTime/depth/depth{3}
histo1Path = Hcal/DigiTask/DigiTime/depth/depth{4}{5}
threshold = 7
yTitle = Mean of Timing - {0} - depth{1} [TS]
"""
#{0} is the name of RBX
#{1} is the depth
#{2} is the vector of depth
#{3} is the first depth
#{4} is the second depth
#{5} is the third depth
template_ini_DIGITiming_2Ddepthchann="""
[plot:DIGITiming-Active-Chan-{0}-depth{1}]
metric = hcal_metrics.RBXCountNonZeroChan('{0}',{2})
relativePath = Hcal/DigiTask/DigiTime/depth/depth{3}
histo1Path = Hcal/DigiTask/DigiTime/depth/depth{4}{5}
threshold = 7
yTitle = Number of Active Channel - {0} - depth{1}
"""

#for DigiTDCTime
#{0} is the name of RBX
template_ini_DIGITDCTime_RBX="""
[plot:DIGITDCTime-MeanTime-{0}]
metric = basic.Mean()
relativePath = Hcal/DigiTask/LETDCTime/SubdetPM/{0}
yTitle = Mean of TDCTime - {0} [ns]
"""
#{0} is the name of RBX
#{1} is the depth name
#{2} is the vector of depth
#{3} is the first depth
#{4} is the second depth
#{5} is the third depth
template_ini_DIGITDCTime_2Ddepth="""
[plot:DIGITDCTime-MeanTime-{0}-depth{1}]
metric = hcal_metrics.RBXMean('{0}',{2})
relativePath = Hcal/DigiTask/LETDCTime/depth/depth{3}
histo1Path = Hcal/DigiTask/LETDCTime/depth/depth{4}{5}
threshold = 7
yTitle = Mean of TDCTime - {0} - depth{1} [ns]
"""
#{0} is the name of RBX
#{1} is the depth
#{2} is the vector of depth
#{3} is the first depth
#{4} is the second depth
#{5} is the third depth
template_ini_DIGITDCTime_2Ddepthchann="""
[plot:DIGITDCTime-Active-Chan-{0}-depth{1}]
metric = hcal_metrics.RBXCountNonZeroChan('{0}',{2})
relativePath = Hcal/DigiTask/LETDCTime/depth/depth{3}
histo1Path = Hcal/DigiTask/LETDCTime/depth/depth{4}{5}
threshold = 7
yTitle = Number of Active Channel - {0} - depth{1}
"""
template_ini_DigiInfor_DeadChan="""
[plot:DIGIInfor-DeadChan-{0}-depth{1}]
metric = hcal_metrics.RBXCountNonZeroChan('{0}',{2})
relativePath = Hcal/DigiRunHarvesting/Dead/depth/depth{3}
histo1Path = Hcal/DigiRunHarvesting/Dead/depth/depth{4}{5}
threshold = 7
yTitle = Number of Dead Channel - {0} - depth{1}
"""

#get the 2D map from files 
#http://cmsdoc.cern.ch/cms/HCALdocs/document/Mapping/Yuan/2020-feb-12/Lmap/
file_name = ["Lmap_ngHB_N_20200212.txt","Lmap_ngHE_N_20200212.txt","Lmap_ngHF_N_20200212.txt","Lmap_ngHO_N_20200212.txt"]
for nfile in file_name:
    with open(nfile, mode='r') as in_file:
        side_idx=0
        eta_idx=0
        phi_idx=0
        depth_idx=0
        rbx_idx=0
        for line in in_file:
            if line[0] == '#':
                orign_line = []
                replace_line = []
                orign_line = line.split(" ")
                for item_line in orign_line:
                    if item_line != '':
                        replace_line.append(item_line)
                for idx in range(len(replace_line)):
                    if replace_line[idx]=='Side':
                        side_idx=idx-1
                    elif replace_line[idx]=='Eta':
                        eta_idx=idx-1
                    elif replace_line[idx]=='Phi':
                        phi_idx=idx-1
                    elif replace_line[idx]=='Depth':
                        depth_idx=idx-1
                    elif replace_line[idx]=='RBX' or replace_line[idx]=='ngRBX':
                        rbx_idx=idx-1
                        #print(side_idx, eta_idx, phi_idx, depth_idx, rbx_idx)
                    continue
            else:
                orign_line = []
                replace_line = []
                orign_line = line.split(" ")
                for item_line in orign_line:
                    if item_line != '':
                        replace_line.append(item_line)
                if replace_line[rbx_idx] in hcal_map_rbx_epd:                                       
                    hcal_map_rbx_epd[replace_line[rbx_idx]].append( (int(replace_line[eta_idx])*int(replace_line[side_idx]),int(replace_line[phi_idx]),int(replace_line[depth_idx])))
                else:
                    hcal_map_rbx_epd[replace_line[rbx_idx]] = [(int(replace_line[eta_idx])*int(replace_line[side_idx]),int(replace_line[phi_idx]),int(replace_line[depth_idx]))]
                #print(replace_line[rbx_idx])
                #print(hcal_map_rbx_epd.keys())

#from 2D map to hist bin number
for rbxname in sorted(set(hcal_map_rbx_epd.keys())):
    if(rbxname!=''):
        hcal_map[rbxname]=[]
    else:
        continue
    eta_phi_dep = hcal_map_rbx_epd[rbxname]
    for eta, phi, dep in eta_phi_dep:
        if eta<42 and eta>-42 and phi>0 and phi<73 and (dep in (1,2,3,4,5,6,7)):
            if rbxname[0:2] == 'HF':
                if eta<0 and int(eta+42)!=0:
                    hcal_map[rbxname].append(( int(eta+42), int(phi), int(dep) ))
                elif eta>0 and int(eta+43)!=0:
                    hcal_map[rbxname].append(( int(eta+43), int(phi), int(dep) ))
                else:
                    print("wierd! eta==0!")
            else:
                if eta<0 and int(eta+43)!=0:
                    hcal_map[rbxname].append(( int(eta+43), int(phi), int(dep) ))
                elif eta>0and int(eta+42)!=0:
                    hcal_map[rbxname].append(( int(eta+42), int(phi), int(dep) ))
                else:
                    print("wierd! eta==0!")
        else:
            print("wierd! eta, phi and dep out of range{0} {1}".format(rbxname,(eta, phi, dep)))

 
                
#hcal rbx map
with open('hcal_metrics.py', mode='w') as out_map:
    out_map.write("from basic import BaseMetric\n#find the map at http://cmsdoc.cern.ch/cms/HCALdocs/document/Mapping/Yuan/2020-feb-12/Lmap\n#HCAL map, rbx -> (eta, phi, depth) \nhcal_map = {\n")
    for rbxname in sorted(set(hcal_map.keys())):
        if rbxname != '':
            out_map.write("        '{0}': {1},\n".format(rbxname, hcal_map[rbxname]))
    out_map.write("}\n")
#mean time wrt rbx
with open('../trendPlotsHcal_DIGITiming_RBX.ini', mode='w') as out_DIGITiming_RBX,\
open('../trendPlotsHcal_DIGITDCTime_RBX.ini', mode='w') as out_DIGITDCTime_RBX:
    for rbxname in RBX_name_rbx:
        out_DIGITiming_RBX.write(template_ini_DIGITiming_RBX.format(rbxname))
        out_DIGITDCTime_RBX.write(template_ini_DIGITDCTime_RBX.format(rbxname))
#mean time wrt rbx and depth
with open('../trendPlotsHcal_DIGITiming_Depth.ini', mode='w') as out_DIGITiming_Depth,\
open('../trendPlotsHcal_DIGITiming_Depth_ActiveChan.ini', mode='w') as out_DIGITiming_Depth_ActiveChan,\
open('../trendPlotsHcal_DIGITDCTime_Depth.ini', mode='w') as out_DIGITDCTime_Depth,\
open('../trendPlotsHcal_DIGITDCTime_Depth_ActiveChan.ini', mode='w') as out_DIGITDCTime_Depth_ActiveChan,\
open('../trendPlotsHcal_DigiInfor_DeadChan.ini', mode='w') as out_DigiInfor_DeadChan:
    for get_key in sorted(set(hcal_map.keys())):
        if get_key != '':
            #depth 12
            out_DIGITiming_Depth.write(template_ini_DIGITiming_2Ddepth.format(get_key,'12',(1,2,0),1,2,''))
            out_DIGITiming_Depth_ActiveChan.write(template_ini_DIGITiming_2Ddepthchann.format(get_key,'12',(1,2,0),1,2,''))
            out_DIGITDCTime_Depth.write(template_ini_DIGITDCTime_2Ddepth.format(get_key,'12',(1,2,0),1,2,''))
            out_DIGITDCTime_Depth_ActiveChan.write(template_ini_DIGITDCTime_2Ddepthchann.format(get_key,'12',(1,2,0),1,2,''))
            out_DigiInfor_DeadChan.write(template_ini_DigiInfor_DeadChan.format(get_key,'12',(1,2,0),1,2,''))
            #depth 34
            out_DIGITiming_Depth.write(template_ini_DIGITiming_2Ddepth.format(get_key,'34',(3,4,0),3,4,''))
            out_DIGITiming_Depth_ActiveChan.write(template_ini_DIGITiming_2Ddepthchann.format(get_key,'34',(3,4,0),3,4,''))
            out_DIGITDCTime_Depth.write(template_ini_DIGITDCTime_2Ddepth.format(get_key,'34',(3,4,0),3,4,''))
            out_DIGITDCTime_Depth_ActiveChan.write(template_ini_DIGITDCTime_2Ddepthchann.format(get_key,'34',(3,4,0),3,4,''))
            out_DigiInfor_DeadChan.write(template_ini_DigiInfor_DeadChan.format(get_key,'34',(3,4,0),3,4,''))
            #depth 56 or 567
            if get_key[0:2] == 'HE':      
                out_DIGITiming_Depth.write(template_ini_DIGITiming_2Ddepth.format(get_key,'567',(5,6,7),5,6,'\nhisto2Path = Hcal/DigiTask/TimingCut/depth/depth7'))
                out_DIGITiming_Depth_ActiveChan.write(template_ini_DIGITiming_2Ddepthchann.format(get_key,'567',(5,6,7),5,6,'\nhisto2Path = Hcal/DigiTask/TimingCut/depth/depth7'))
                out_DIGITDCTime_Depth.write(template_ini_DIGITDCTime_2Ddepth.format(get_key,'567',(5,6,7),5,6,'\nhisto2Path = Hcal/DigiTask/LETDCTime/depth/depth7'))
                out_DIGITDCTime_Depth_ActiveChan.write(template_ini_DIGITDCTime_2Ddepthchann.format(get_key,'567',(5,6,7),5,6,'\nhisto2Path = Hcal/DigiTask/LETDCTime/depth/depth7'))
                out_DigiInfor_DeadChan.write(template_ini_DigiInfor_DeadChan.format(get_key,'567',(5,6,7),5,6,'\nhisto2Path = Hcal/DigiRunHarvesting/Dead/depth/depth7'))
            else:      
                out_DIGITiming_Depth.write(template_ini_DIGITiming_2Ddepth.format(get_key,'56',(5,6,0),5,6,''))
                out_DIGITiming_Depth_ActiveChan.write(template_ini_DIGITiming_2Ddepthchann.format(get_key,'56',(5,6,0),5,6,''))
                out_DIGITDCTime_Depth.write(template_ini_DIGITDCTime_2Ddepth.format(get_key,'56',(5,6,0),5,6,''))
                out_DIGITDCTime_Depth_ActiveChan.write(template_ini_DIGITDCTime_2Ddepthchann.format(get_key,'56',(5,6,0),5,6,''))
                out_DigiInfor_DeadChan.write(template_ini_DigiInfor_DeadChan.format(get_key,'56',(5,6,0),5,6,''))


                
                
                

temp_js_DIGITiming_RBX="""\
        {{
            name: "DIGITiming-MeanTime",
            plot_title: "DIGITiming",
            y_title: "Mean of DIGITiming [TS]",
            subsystem: "HCAL",
            correlation: false,
            series: {0},
        }},\n"""
temp_js_DIGITiming_2Ddepth="""\
        {{
            name: "DIGITiming-MeanTime-{0}-depth{1}",
            plot_title: "DIGITiming MeanTime {0} depth{1}",
            y_title: "Mean of DIGITiming [TS]",
            subsystem: "HCAL",
            correlation: false,
            series: {2},
        }},\n"""
temp_js_DIGITiming_2Ddepthchann="""\
        {{
            name: "DIGITiming-Active-Chan-{0}-depth{1}",
            plot_title: "DIGITiming Active Chan {0} depth{1}",
            y_title: "Number of Active Channel",
            subsystem: "HCAL",
            correlation: false,
            series: {2},
        }},\n"""
temp_js_DIGITDCTime_RBX="""\
        {{
            name: "DIGITDCTime-MeanTime",
            plot_title: "DIGITDCTime",
            y_title: "Mean of DIGITDCTime [ns]",
            subsystem: "HCAL",
            correlation: false,
            series: {0},
        }},\n"""
temp_js_DIGITDCTime_2Ddepth="""\
        {{
            name: "DIGITDCTime-MeanTime-{0}-depth{1}",
            plot_title: "DIGITDCTime MeanTime {0} depth{1}",
            y_title: "Mean of DIGITDCTime [ns]",
            subsystem: "HCAL",
            correlation: false,
            series: {2},
        }},\n"""
temp_js_DIGITDCTime_2Ddepthchann="""\
        {{
            name: "DIGITDCTime-Active-Chan-{0}-depth{1}",
            plot_title: "DIGITDCTime Active Chan {0} depth{1}",
            y_title: "Number of Active Channel",
            subsystem: "HCAL",
            correlation: false,
            series: {2},
        }},\n"""
temp_js_DigiInfor_DeadChan="""\
        {{
            name: "DIGIInfor-DeadChan-{0}-depth{1}",
            plot_title: "Dead Chan {0} depth{1}",
            y_title: "Number of Dead Channel",
            subsystem: "HCAL",
            correlation: false,
            series: {2},
        }},\n"""

plot_name_DIGITiming_RBX = '['
plot_name_DIGITDCTime_RBX = '['
plot_name_DIGITiming_RBX_series = '"DIGITiming-MeanTime-{0}",'
plot_name_DIGITDCTime_RBX_series = '"DIGITDCTime-MeanTime-{0}",'

plot_name_DIGITiming_2Ddepth = '['
plot_name_DIGITiming_2Ddepthchann = '['
plot_name_DIGITDCTime_2Ddepth = '['
plot_name_DIGITDCTime_2Ddepthchann = '['
plot_name_DigiInfor_DeadChan = '['

plot_name_DIGITiming_2Ddepth_series = '"DIGITiming-MeanTime-{0}-depth{1}",'
plot_name_DIGITiming_2Ddepthchann_series = '"DIGITiming-Active-Chan-{0}-depth{1}",'
plot_name_DIGITDCTime_2Ddepth_series = '"DIGITDCTime-MeanTime-{0}-depth{1}",'
plot_name_DIGITDCTime_2Ddepthchann_series = '"DIGITDCTime-Active-Chan-{0}-depth{1}",'
plot_name_DigiInfor_DeadChan_series = '"DIGIInfor-DeadChan-{0}-depth{1}",'


#group display 
with open('display.js', mode='w') as out_js:
    plot_name_DIGITiming_RBX = '['
    plot_name_DIGITDCTime_RBX = '['
    for sub_d in RBX_name_rbx:
        plot_name_DIGITiming_RBX += plot_name_DIGITiming_RBX_series.format(sub_d)
        plot_name_DIGITDCTime_RBX += plot_name_DIGITDCTime_RBX_series.format(sub_d)
    plot_name_DIGITiming_RBX=plot_name_DIGITiming_RBX[0:-1] + ']'
    plot_name_DIGITDCTime_RBX=plot_name_DIGITDCTime_RBX[0:-1] + ']'
    out_js.write(temp_js_DIGITiming_RBX.format(plot_name_DIGITiming_RBX))
    out_js.write(temp_js_DIGITDCTime_RBX.format(plot_name_DIGITDCTime_RBX))
    for sub_d in RBX_name_depth:
        for dp in (12,34,56):
            plot_name_DIGITiming_RBX = '['
            plot_name_DIGITiming_2Ddepth = '['
            plot_name_DIGITiming_2Ddepthchann = '['
            plot_name_DIGITDCTime_RBX = '['
            plot_name_DIGITDCTime_2Ddepth = '['
            plot_name_DIGITDCTime_2Ddepthchann = '['
            plot_name_DigiInfor_DeadChan = '['
            for get_key in sorted(set(hcal_map.keys())):
                if get_key[0:3] == sub_d[0:3]:
                    if get_key[0:2]=='HE' and dp==56:
                        dp=567
                    plot_name_DIGITiming_2Ddepth += plot_name_DIGITiming_2Ddepth_series.format(get_key,dp)
                    plot_name_DIGITiming_2Ddepthchann += plot_name_DIGITiming_2Ddepthchann_series.format(get_key,dp)
                    plot_name_DIGITDCTime_2Ddepth += plot_name_DIGITDCTime_2Ddepth_series.format(get_key,dp)
                    plot_name_DIGITDCTime_2Ddepthchann += plot_name_DIGITDCTime_2Ddepthchann_series.format(get_key,dp)
                    plot_name_DigiInfor_DeadChan += plot_name_DigiInfor_DeadChan_series.format(get_key,dp)
            plot_name_DIGITiming_2Ddepth=plot_name_DIGITiming_2Ddepth[0:-1] + ']'
            plot_name_DIGITiming_2Ddepthchann=plot_name_DIGITiming_2Ddepthchann[0:-1] + ']'
            plot_name_DIGITDCTime_2Ddepth=plot_name_DIGITDCTime_2Ddepth[0:-1] + ']'
            plot_name_DIGITDCTime_2Ddepthchann=plot_name_DIGITDCTime_2Ddepthchann[0:-1] + ']'
            plot_name_DigiInfor_DeadChan=plot_name_DigiInfor_DeadChan[0:-1] + ']'
            out_js.write(temp_js_DIGITiming_2Ddepth.format(sub_d,dp,plot_name_DIGITiming_2Ddepth))
            out_js.write(temp_js_DIGITiming_2Ddepthchann.format(sub_d,dp,plot_name_DIGITiming_2Ddepthchann))
            out_js.write(temp_js_DIGITDCTime_2Ddepth.format(sub_d,dp,plot_name_DIGITDCTime_2Ddepth))
            out_js.write(temp_js_DIGITDCTime_2Ddepthchann.format(sub_d,dp,plot_name_DIGITDCTime_2Ddepthchann))
            out_js.write(temp_js_DigiInfor_DeadChan.format(sub_d,dp,plot_name_DigiInfor_DeadChan))
        
        
        
