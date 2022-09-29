# This file contains logic to handle the new management REST attach detach flow
# TODO: This serves as an extention to the NVMeshSDK until this feature is implemented in the SDK
import consts
from NVMeshSDK.APIs.ClientAPI import ClientAPI

class NewClientAPI(ClientAPI):
    def attach(self, clientID, volume, access_mode, preempt=False, postTimeout=None):
        volumes = [{
            "name": volume,
            "reservation": {
                "mode": access_mode,
                "preempt": preempt
            }
        }]

        req = {
            'client': clientID,
            'volumes': volumes,
        }
        return self.makePost(['attach'], req, postTimeout=postTimeout)

    def detach(self, clientID, volume, force, postTimeout=None):
        volumes = [{
            "name": volume,
            "force": 1 if force else 0
        }]

        req = {
            'client': clientID,
            'volumes': volumes,
        }
        return self.makePost(['detach'], req, postTimeout=postTimeout)


if __name__ == "__main__":
    vol_id = "csi-a5a0a6b6-5695-445a"
    c = NewClientAPI(managementServers="nvme115:4000", managementProtocol='https')
    #err, b = c.attach(clientID="nvme115", volume=vol_id, access_mode="SHARED_READ_WRITE")
    err, b = c.detach(clientID="nvme117", volume=vol_id, force=True)
    print(err)
    print(">>>>>>>>>>")
    print(b)