'''
This file contains helper f(x)s when conduction tests that includes Manifest models
'''
from manifests.models import *
from address.models import *

def createComputeHardware(hardware):
    """
    Helper function which populates compute hardware test data.
    """
    for item in hardware:
        compute_hardware = ComputeHardware.objects.create(
            hardware=item["hardware"], 
            hw_model=item["hw_model"],
            manufacturer=item['manufacturer']
        )

        if "capabilities" in item:
            for name in item["capabilities"]:
                capability, _ = Capability.objects.get_or_create(capability=name)
                compute_hardware.capabilities.add(capability)

def createSensorHardware(hardware):
    """
    Helper function which populates sensor hardware test data.
    """
    for item in hardware:
        sensor_hardware = SensorHardware.objects.create(
            hardware=item["hardware"], 
            hw_model=item["hw_model"],
            manufacturer=item['manufacturer']
        )

        if "capabilities" in item:
            for name in item["capabilities"]:
                capability, _ = Capability.objects.get_or_create(capability=name)
                sensor_hardware.capabilities.add(capability)

def createLorawanDevice(device):
    """
    Helper function which populates lorawan device test data.
    """
    for item in device:
        LorawanDevice.objects.create(
            deveui=item["deveui"], name=item["name"], 
            hardware=SensorHardware.objects.get(hardware=item["hardware"])
        )

def createProject(project):
    """
    Helper function which populates project test data.
    """
    for item in project:
        NodeBuildProject.objects.create(
            name=item['name']
        )

def createFocus(focus):
    """
    Helper function which populates focus test data.
    """
    for item in focus:
        NodeBuildProjectFocus.objects.create(
            name=item['name']
        )

def createPartner(partner):
    """
    Helper function which populates partner test data.
    """
    for item in partner:
        NodeBuildProjectPartner.objects.create(
            name=item['name']
        )

def createSite(site):
    """
    Helper function which populates site test data.
    """
    for item in site:
        Site.objects.create(
            id=item['id'], description=item['description']
        )

def createAddress(address):
    """
    Helper function which populates address test data.
    """
    for item in address:
        Country.objects.get_or_create(
            name= item['country'], code=item['country_code']
        )

        State.objects.get_or_create(
            name= item['state'], code=item['state_code'],
            country=Country.objects.get(name=item['country'])
        )

        Locality.objects.get_or_create(
            name= item['town'], postal_code=item['postal_code'],
            state=State.objects.get(name=item['state'])
        )

        Address.objects.get_or_create(
            street_number=item['streetnum'],route=item['route'], formatted=item['formatted'],
            locality=Locality.objects.get(postal_code=item['postal_code'])
        )

def createModem(modem):
    """
    Helper function which populates modem test data.
    """        
    for item in modem:
        Modem.objects.create(
            imei=item['imei'],imsi=item['imsi'],
            iccid=item['iccid'],carrier=item['carrier'],
            model=item['model'],sim_type=item['sim_type']
        )

def createManifests(manifests):
    """
    Helper function which populates manifest test data.
    """
    for manifest in manifests:
        node_obj = NodeData.objects.create(
            vsn=manifest["vsn"],
            name=manifest["name"],
            gps_lat=manifest["gps_lat"],
            gps_lon=manifest["gps_lon"],
            gps_alt=manifest["gps_alt"],
            project=NodeBuildProject.objects.get(name=manifest['project']),
            focus=NodeBuildProjectFocus.objects.get(name=manifest['focus']),
            partner=NodeBuildProjectPartner.objects.get(name=manifest['partner']),
            type=manifest['type'],
            site_id=Site.objects.get(id=manifest['site_id']),
            address=Address.objects.get(formatted=manifest['addr_formatted']),
            location=manifest["location"],
            phase=manifest['phase'],
            commissioned_at=manifest['commissioned_at'],
            registered_at=manifest['registered_at']
        )
        #update modem
        modem = Modem.objects.get(sim_type=manifest['modem_sim'])
        modem.node = node_obj
        modem.save()
        for sensor in manifest['sensors']:
            if "lorawan" in sensor['capabilities']:
                LorawanConnection.objects.create(
                    node=node_obj,
                    connection_type="OTAA", #in this view con_type does not matter so set a static val
                    lorawan_device=LorawanDevice.objects.get(name=sensor['name'])
                )
            else:
                NodeSensor.objects.create(
                    node=node_obj,
                    name=sensor['name'],
                    hardware=SensorHardware.objects.get(hw_model=sensor['hw_model'])
                )
        for compute in manifest["computes"]:
            compute_obj = Compute.objects.create(
                node=node_obj,
                hardware=ComputeHardware.objects.get(hw_model=compute["hw_model"]),
                name=compute["name"],
            )