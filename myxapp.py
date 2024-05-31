import src.e2ap_xapp as e2ap_xapp
#from ran_messages_pb2 import *
from time import sleep
from ricxappframe.e2ap.asn1 import IndicationMsg

import sys
sys.path.append("oai-oran-protolib/builds/")
from ran_messages_pb2 import *
import csv




def xappLogic():

    # instanciate xapp 
    connector = e2ap_xapp.e2apXapp()

    # get gnbs connected to RIC
    gnb_id_list = connector.get_gnb_id_list()
    print("{} gNB connected to RIC, listing:".format(len(gnb_id_list)))
    for gnb_id in gnb_id_list:
        print(gnb_id)
    print("---------")

    # subscription requests
    for gnb in gnb_id_list:
        e2sm_buffer = e2sm_report_request_buffer()
        connector.send_e2ap_sub_request(e2sm_buffer,gnb)
        #connector.send_e2ap_control_request(e2sm_buffer,gnb)
    
    # read loop
    elapsed_time = 0
    sleep_time = 0.5
    while True:
        print("Sleeping {}ms...".format(sleep_time*1000))
        sleep(sleep_time)
        elapsed_time += sleep_time
        messgs = connector.get_queued_rx_message()
        if len(messgs) == 0:
            print("{} messages received while waiting".format(len(messgs)))
            print("____")
        else:
            print("{} messages received while waiting, printing:".format(len(messgs)))
            for msg in messgs:
                if msg["message type"] == connector.RIC_IND_RMR_ID:
                    print("RIC Indication received from gNB {}, decoding E2SM payload".format(msg["meid"]))
                    indm = IndicationMsg()
                    indm.decode(msg["payload"])
                    resp = RAN_indication_response()
                    resp.ParseFromString(indm.indication_message)
                    # print meas_rsrp for each element, consider the protobuf file
                    for ue in resp.param_map[1].ue_list.ue_info:
                        print("RNTI: {}".format(ue.rnti))
                        print("-- RSRP: {}".format(ue.meas_rsrp))
                        print("-- BER DL: {}".format(ue.meas_ber_down))
                        print("-- BER UP: {}".format(ue.meas_ber_up))
                        print("-- MCS DL: {}".format(ue.meas_mcs_down))
                        print("-- MCS UP: {}".format(ue.meas_mcs_up))
                        print("Cell load (PRB): {}".format(resp.param_map[2].int64_value))
                        print("Elapsed time: {}".format(elapsed_time))

                        filename = f"UE_{ue.rnti}.csv"
                        #write the header if file is empty
                        with open(filename, 'a') as f:
                            if f.tell() == 0:
                                writer = csv.writer(f)
                                # write the rnti
                                writer.writerow(["RNTI"])
                                writer.writerow([ue.rnti])
                                writer.writerow([])
                                writer.writerow(["Time", "RSRP", "BER_DL", "BER_UP", "MCS_DL", "MCS_UP", "Cell_load_alloc_PRB"])
                            #write the data
                            writer = csv.writer(f)
                            writer.writerow([elapsed_time, ue.meas_rsrp, ue.meas_ber_down, ue.meas_ber_up, ue.meas_mcs_down, ue.meas_mcs_up, resp.param_map[2].int64_value])
                        print("___")

                    #print(resp)
                    print("___")
                else:
                    print("Unrecognized E2AP message received from gNB {}".format(msg["meid"]))

def e2sm_report_request_buffer():
    master_mess = RAN_message()
    master_mess.msg_type = RAN_message_type.INDICATION_REQUEST
    inner_mess = RAN_indication_request()
    inner_mess.target_params.extend([RAN_parameter.GNB_ID, RAN_parameter.UE_LIST, RAN_parameter.GNB_PRB])
    master_mess.ran_indication_request.CopyFrom(inner_mess)
    buf = master_mess.SerializeToString()
    return buf

if __name__ == "__main__":
    xappLogic()