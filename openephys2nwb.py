from pynwb import NWBFile, TimeSeries, NWBHDF5IO, ecephys
from pynwb.file import Subject
from datetime import datetime
import json
from OpenEphys import load
import re
import os
from dateutil import parser
from defaults import default_metadata

def convertOpenEphystoNWB(ephys_filePath, save_path):
    
    """
    main converter: receives opene ephys directory and saves nwb file to specified directory
    
    """
    
    
    filePath = ephys_filePath
    create_date = datetime.now()
    metadata = {}

    """
    if no metadata file found in directory, default metadata dictionary is used,'
    default initialises most things to empty
    """
    
    if 'metadata.txt' in os.listdir(filePath):
      metadata = readMetaData( os.path.join(filePath, 'metadata.txt') )
    else:
      for files in os.listdir(filePath):
        metadata = default_metadata
        metadata[files] = [0]

    nwbfile = NWBFile( str(metadata['session']['description']) , 'NWB_out', 
                      parser.parse(metadata['session']['start_time']),
                      file_create_date = create_date )

    device = nwbfile.create_device(name = str(metadata['session']['device_name']) )

    electrode_name = str(metadata['electrode_group']['name'])
    description = str(metadata['electrode_group']['description'])
    location = str(metadata['electrode_group']['location'])

    electrode_group = nwbfile.create_electrode_group(electrode_name,
                                                    description=description,
                                                    location=location,
                                                    device=device)

    for electrode_metadata in metadata['electrode_metadata']:
        nwbfile.add_electrode(id= int(electrode_metadata['id']),
                              x= float(electrode_metadata['x']), 
                              y= float(electrode_metadata['y']), 
                              z= float(electrode_metadata['z']),
                              imp= float(electrode_metadata['impedance']),
                              location= str(electrode_metadata['location']), 
                              filtering=  str(electrode_metadata['filtering']),
                              group=electrode_group)
    
    """
    
    individual files are loaded and stored in nwb one at a time.
    
    .continuous files are stored in electrical series.
    .spike are stored in spike event series.
    
    """
    
    for files in os.listdir(filePath):

        if files.endswith('.continuous'):

            electrode_table_region = nwbfile.create_electrode_table_region( 
                                      json.loads(metadata['file_electrodes'][str(files)]) 
                                      , str(files)+' electrodes' )

            r = load(os.path.join(filePath, files))

            dat = TimeSeries(name = "continuous_"+r['header']['channel'],  data = r['data'],   unit = 'V',
                      starting_time=0.0, rate=float(r['header']['sampleRate']),
                      conversion=r['header']['bitVolts'])
            
            cont_dat = ecephys.ElectricalSeries(name = "continuous_"+r['header']['channel'],
                                                data = dat,
                                                electrodes = electrode_table_region,
                                                rate=float(r['header']['sampleRate'] )  )

            nwbfile.add_acquisition(cont_dat )

        elif files.endswith('.spikes'):
            
            electrode_table_region = nwbfile.create_electrode_table_region( 
                                    json.loads(metadata['file_electrodes'][str(files)]) 
                                    , str(files)+' electrodes' )

            r = load(os.path.join(filePath, files))

            dat = TimeSeries(name = r['header']['electrode'], data = r['spikes'], unit = 'V',
                                    starting_time=0.0, rate=float(r['header']['sampleRate']),
                                    ) 
            
            spike_dat = ecephys.SpikeEventSeries(name = r['header']['electrode'],
                                                data = dat,
                                                timestamps = r['timestamps'],
                                                electrodes = electrode_table_region)
            
            nwbfile.add_acquisition( spike_dat )

    io = NWBHDF5IO( save_path, mode='w')
    io.write(nwbfile)
    io.close()
    
    
def readMetaData(filepath):

  """
    metadata files are txt files which contain electrode metadata needed to create 
    electrical and spike event series in nwb.
    
    this function parses the metadata file to return a dictionary which is used in the main converter.
    
    metadata includes the name of the device used, and individual elctrode locations, names etc.
  """
  session = {}
  electrode_group = {}
  electrode_metadata = []
  file_electrodes = {}

  lines = []

  with open( filepath ) as f:
    lines = f.readlines()

  for line in lines:
    
    if line.split('.')[0] == 'session':
      s = line.replace('\n','').replace('session.','').replace(';','')

      session[s.split(' = ')[0]] = s.split(' = ')[1]

    elif line.split('.')[0] == 'electrode_group':
      s = line.replace('\n','').replace('electrode_group.','').replace(';','')

      electrode_group[s.split(' = ')[0]] = s.split(' = ')[1]
      
    elif re.match(r"electrode\d+_metadata", line.split('.')[0] ):
      s = line.replace('\n','').replace(line.split('.')[0]+'.','').replace(';','')

      if s.split(' = ')[0] == 'id':
        electrode_meta = {}
        electrode_meta[s.split(' = ')[0]] = s.split(' = ')[1]
        electrode_metadata.append( electrode_meta )
      else:
        electrode_metadata[-1][s.split(' = ')[0]] = s.split(' = ')[1]

    elif line.split('.')[0] == 'file_electrodes':
      s = line.replace('\n','').replace('file_electrodes.','').replace(';','')

      file_electrodes[s.split(' = ')[0]] = s.split(' = ')[1]

  metadata = {}
  metadata['session'] = session
  metadata['electrode_group'] = electrode_group
  metadata['electrode_metadata'] = electrode_metadata
  metadata['file_electrodes'] = file_electrodes

  return (metadata)
