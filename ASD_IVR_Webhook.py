import requests, json
import traceback
import re

Informatica_validationUrl   = "https://usw1-apigw.dm1-us.informaticacloud.com/t/prod.ttec.com/validate-oid?oracle_id="
Informatica_ValidationAuth  = "Basic a29yZS5haS5wcm9kOmswcjNAMWIwdA=="
Asknow_url = "https://asknowdev.service-now.com"
Asknow_Auth = "Basic ZXllU2hhcmVfSW50ZWdyYXRvcjpUZWxldGVjaEAx"
Email_url="https://usw1-apigw.dm1-us.informaticacloud.com/t/ttec.com/chatbot-send-email"
Email_auth="Basic a29yZS5haS5kZXY6azByM0AxYjB0"
escalation_skill = {
"Hard_PC_Prod":23,
"Easy_Prod":24,
"Hard_PC_Other":37,
"Easy_Other":36,
"Hard_Stick_Other":25,
"Hard_Stick_Prod":35,
"iGel":26,
"FEMA_Helpdesk":31,
"GSD_Outage":27,
"GSD_Callback":28,
"GSD_Helpdesk":29,
"GSD_Password":30,
"GSD_FEMA_Password":32,
"GSD_FEMA_Helpdesk":33,
"GSD_FEMA_Emergency":34
}



def ivr_apis(request):
    try:
        #req = request.get_json()
        req = request
        tag = req["fulfillmentInfo"]["tag"]

        ################################################################################
        if (tag=="UserValidation" or tag=="uservalidation"):   #user validation module
         oracle_id = req["sessionInfo"]["parameters"]["oracleid"]
         oracle_id1 = oracle_id.strip() #trim
         oracle_id2 = re.sub(r"[^0-9]", '', oracle_id1) #remove characters
         RegexMatch =re.match(r"^\d{7}$", oracle_id2)   #regex match
         if RegexMatch:
		      #headers
          headers = {'Authorization': Informatica_ValidationAuth}
          UserValidationResponse = requests.request("GET", Informatica_validationUrl+oracle_id2, headers=headers)
          if UserValidationResponse.status_code == 200:
            UserValidationResponsetext = json.loads(UserValidationResponse.text)
            if UserValidationResponsetext["message"]=="Success":
              u_ccode=UserValidationResponsetext["result"]["client_code"]
              if (u_ccode=="2525" or u_ccode=="2763" or u_ccode=="2764" or u_ccode=="2772"):
                 FEMAuser = "yes"
                 prodUser = "yes"
                 skipTicket = "yes"
              else:
                 FEMAuser = "no"
                 prodUser = "no"
                 skipTicket = "no"
              u_segment= UserValidationResponsetext["result"]["segment"]
              if "Engage" in u_segment:
                orgName="Engage"
              else:
                orgName="Digital"
              agent_lob=UserValidationResponsetext["result"]["client_name"]
              if "ebay" in agent_lob.lower():          #igel check
                iGel="true"
              else:
                iGel="false"
              res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Success",
                    "userName":UserValidationResponsetext["result"]["emp_name"],
                    "userCountry":UserValidationResponsetext["result"]["country_code"],
                    "userEmail":UserValidationResponsetext["result"]["work_email"],
                    "agent_lob":agent_lob,
                    "employeeType":UserValidationResponsetext["result"]["emp_type"],
                    "oracle_id":UserValidationResponsetext["result"]["oracle_id"],
                    "iGel":iGel,
                    "orgName":orgName,
                    "FEMAuser":FEMAuser,
                    "prodUser":prodUser,
                    "skipTicket":skipTicket
                   },
                  },
                }  
            elif UserValidationResponsetext["message"]=="Multiple records found":
              res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Multiple records found"
                    },
                   },
                  }
            elif UserValidationResponsetext["message"]=="Record not found":
              res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Not Found",
                    "oracle_id":oracle_id2
                    },
                   },
                  }
            else:
              res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Not Found",
                    "oracle_id":oracle_id2
                    },
                   },
                  }
          else:
            res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "API Failure"
                 },
               },
             }
         else:
          res = {
            "sessionInfo": {
                "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Invalid_ID"
                 },
             },
           }


         ################################################################################
        elif (tag=="getBSSysId" or tag=="getbssysid"):   #fetch business Service SysID module
         oracle_id = req["sessionInfo"]["parameters"]["oracle_id"]
         headers = {'Authorization': Asknow_Auth}
         GetSysIDResponse = requests.request("GET", Asknow_url+"/api/now/table/sys_user?sysparm_fields=u_business_service,u_business_service.sys_id, manager,sys_id,u_imported_location,u_imported_costing_client_code,u_job_family&sysparm_limit=1&employee_number="+oracle_id+"&sysparm_display_value=true&sysparm_exclude_reference_link=true", headers=headers)
         if GetSysIDResponse.status_code==200:
           GetSysIDResponsetext = json.loads(GetSysIDResponse.text)
           if GetSysIDResponsetext["result"]:
             res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Success",
                    "bsSysID":GetSysIDResponsetext["result"][0]["u_business_service.sys_id"],
                    "userSysID":GetSysIDResponsetext["result"][0]["sys_id"]
                  },
                 },
                }
           else:
             res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Invalid_ID"
                 },
               },
             }
         else:
           res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "API Failure"
                 },
               },
             }


         ################################################################################
        elif (tag=="checkOutage" or tag=="checkoutage"):   #check outage module
         bsSysID = req["sessionInfo"]["parameters"]["bsSysID"]
         headers = {'Authorization': Asknow_Auth}
         GetOutageResponse = requests.request("GET", Asknow_url+"/api/now/table/cmdb_ci_outage?sysparm_fields=number, task_number.number, task_number.sys_id, task_number.state,task_number.short_description,task_number.u_outage_flag,task_number.cmdb_ci,task_number.u_symptoms_category,task_number.u_application,duration,sys_class_name,task_number.u_client_side_issue, task_number.priority&sysparm_query=cmdb_ci="+bsSysID+"^task_number.stateIN1,2^task_number.priorityIN1,2^type=outage^sys_class_name=cmdb_ci_outage", headers=headers)
         if GetOutageResponse.status_code==200:
           GetOutageResponsetext = json.loads(GetOutageResponse.text)
           if GetOutageResponsetext["result"]:
             res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Outage Found",
                    "outageTicket":"deflect",
                    "checkOutage":"outage",
                    "outagebusinessServiceValue":"86ba01486f742d88f7cf04b0be3ee4c2",
                    "outageincNum":"INC16447732",
                    "outageShortDescription":"there is an outage",
                    "outageSymptomsCategory":"Application Other",
                    "outageApplication":"Humanify"
                 },
               },
             }
           else:
             res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "No Outage"
                 },
               },
             }
         else:
           res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "API Failure"
                 },
               },
             }

         ################################################################################
        elif (tag=="recentTicket" or tag=="recentticket"):   #check recent ticket module
         oracle_id = req["sessionInfo"]["parameters"]["oracle_id"]
         headers = {'Authorization': Asknow_Auth}
         GetRecentTicketResponse = requests.request("GET", Asknow_url+"/api/now/table/incident?sysparm_limit=1&sysparm_fields=sys_id,number,assignment_group.name,u_ttdbot,short_description,state,close_notes,sys_updated_on&sysparm_query=sys_updated_on[Relative On or before]javascript:gs.daysAgo(3)^active=true^caller_id.employee_number="+oracle_id, headers=headers)
         if GetRecentTicketResponse.status_code==200:
           GetRecentTicketResponsetext = json.loads(GetRecentTicketResponse.text)
           if GetRecentTicketResponsetext["result"]:
             ticketState=GetRecentTicketResponsetext["result"][0]["state"]
             ttdFlag=GetRecentTicketResponsetext["result"][0]["u_ttdbot"]
             recentTicket=GetRecentTicketResponsetext["result"][0]["number"]
             shortDescription=GetRecentTicketResponsetext["result"][0]["short_description"]
             prevTicketType=GetRecentTicketResponsetext["result"][0]["assignment_group.name"]
             if ttdFlag == "true":
              ttdBotTicket="yes"
             else:
              ttdBotTicket="no"
             if prevTicketType == "AtHome Service Desk":
              prevTicketAG="ASD"
             else:
              prevTicketAG="other"
             if ticketState == "1":
              ticketStatus="Your ticket is now on queue and will be worked on by our technical team"
             elif ticketState == "2":
              ticketStatus="Your ticket is still active and being worked on by our technical team"              
             else:
              ticketStatus="Your ticket is on awaiting status and waiting for additional information from you"

             if ticketState == "6" or ticketState =="7":
               res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "No Ticket Found"
                   },
                  },
                }
             else:
               res = {
                 "sessionInfo": {
                    "parameters": {
                      "Webhook_Error": "false",
                      "Response_Value": "Ticket Found",
                      "ttdBotTicket":ttdBotTicket,
                      "ticketStatus":ticketStatus,
                      "prevTicketAG":prevTicketAG,
                      "recentTicket":recentTicket,
                      "shortDescription":shortDescription
                   },
                 },
               }
           else:
             res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "No Ticket Found"
                 },
               },
             }
         else:
           res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "API Failure"
                 },
               },
             }


         ###########################################################################      
        elif (tag=="getsysid" or tag=="getSysID"):   #get user sys id
          oracle_id = req["sessionInfo"]["parameters"]["oracle_id"]
          authenticated = req["sessionInfo"]["parameters"]["authenticated"]
          if authenticated == "true":
            headers = {'Authorization': Asknow_Auth}
            GetsysIDResponse = requests.request("GET", Asknow_url+"/api/now/table/sys_user?sysparm_query=employee_number="+oracle_id+"^active=true^user_nameISNOTEMPTY&sysparm_fields=sys_id, u_imported_location,location,manager,u_business_service&sysparm_limit=1&sysparm_exclude_reference_link=true", headers=headers)
            if GetsysIDResponse.status_code==200:
              GetsysIDResponsetext= json.loads(GetsysIDResponse.text)
              if GetsysIDResponsetext["result"]:
                res = {
                  "sessionInfo": {
                     "parameters": {
                       "Webhook_Error": "false",
                       "Response_Value": "ID Found",
                       "userSysID":GetsysIDResponsetext["result"][0]["sys_id"],
                       "userBS":GetsysIDResponsetext["result"][0]["u_business_service"],
                       "userManager":GetsysIDResponsetext["result"][0]["manager"],
                       "userLocation":GetsysIDResponsetext["result"][0]["location"]
                    },
                  },
                }
              else:
                res = {
                  "sessionInfo": {
                     "parameters": {
                       "Webhook_Error": "false",
                       "Response_Value": "ID not found",
                       "userSysID":"b2f0fcfc87dc115060b0a9783cbb3580",
                       "userBS":"86ba01486f742d88f7cf04b0be3ee4c2",
                       "uLobSite":"aa9222cb6fec9100ac14373aea3ee491",
                       "userLocation":""
                    },
                  },
                }
            else:
              res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "API Failure"
                    },
                  },
                }
          else:
              res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "ID not found",
                    "userSysID":"b2f0fcfc87dc115060b0a9783cbb3580",
                    "userBS":"86ba01486f742d88f7cf04b0be3ee4c2",
                    "uLobSite":"aa9222cb6fec9100ac14373aea3ee491",
                    "userLocation":""
                    },
                  },
                }








         ################################################################################       
        elif (tag=="getLobSite" or tag=="getlobsite"):   #get lob site
          userLocation = req["sessionInfo"]["parameters"]["userLocation"]
          authenticated = req["sessionInfo"]["parameters"]["authenticated"]
          if authenticated == "true":
            headers = {'Authorization': Asknow_Auth}
            GetLobSiteResponse = requests.request("GET", Asknow_url+"/api/now/table/cmn_location?sysparm_fields=u_lobsite.u_site,u_lobsite&sysparm_limit=10&sysparm_exclude_reference_link=true&sys_id="+userLocation, headers=headers)
            if GetLobSiteResponse.status_code==200:
              GetLobSiteResponsetext= json.loads(GetLobSiteResponse.text)
              if GetLobSiteResponsetext["result"]:
                res = {
                  "sessionInfo": {
                     "parameters": {
                       "Webhook_Error": "false",
                       "Response_Value": "ID Found",
                       "uLobSite":GetLobSiteResponsetext["result"][0]["u_lobsite"]
                    },
                  },
                }
              else:
                res = {
                  "sessionInfo": {
                     "parameters": {
                       "Webhook_Error": "false",
                       "Response_Value": "ID not found",
                       "userSysID":"b2f0fcfc87dc115060b0a9783cbb3580",
                       "userBS":"86ba01486f742d88f7cf04b0be3ee4c2",
                       "uLobSite":"aa9222cb6fec9100ac14373aea3ee491",
                       "userLocation":""
                    },
                  },
                }
            else:
              res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "API Failure"
                    },
                  },
                }
          else:
              res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "ID not found",
                    "userSysID":"b2f0fcfc87dc115060b0a9783cbb3580",
                    "userBS":"86ba01486f742d88f7cf04b0be3ee4c2",
                    "uLobSite":"aa9222cb6fec9100ac14373aea3ee491",
                    "userLocation":""
                    },
                  },
                }


         ################################################################################ 
        elif (tag=="createTicket" or tag=="createticket"): # create asknow ticket


          if "description" in req["sessionInfo"]["parameters"]:
            description = req["sessionInfo"]["parameters"]["description"]
          else:
            description = req["sessionInfo"]["parameters"]["shortDescription"]


          headers = {'Authorization': Asknow_Auth}
          payload = {
                 "caller_id": req["sessionInfo"]["parameters"]["userSysID"],
                 "u_client_lob": req["sessionInfo"]["parameters"]["userBS"],
                 "u_lob_site": req["sessionInfo"]["parameters"]["uLobSite"],
                 "contact_type": "Phone",
                 "short_description": req["sessionInfo"]["parameters"]["shortDescription"],
                 "description": description,
                 "assignment_group" : req["sessionInfo"]["parameters"]["assignmentGroup"],
                 "u_responsible_group" : "Automation Service - AAH",
                 "watch_list" : req["sessionInfo"]["parameters"]["userManager"],
            }
          createIncidentResponse = requests.request("POST", Asknow_url+"/api/now/table/incident", headers=headers,json=payload)
          if createIncidentResponse.status_code==201:
              createIncidentResponsetext= json.loads(createIncidentResponse.text)
              if createIncidentResponsetext["result"]:
                res = {
                 "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Ticket Created",
                    "ticketNumber":createIncidentResponsetext["result"]["number"],
                    "ticketSysID":createIncidentResponsetext["result"]["sys_id"]
                    },
                  },
                }
              else:
                res = {
                 "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Not Created"
                    },
                  },
                }
          else:
              res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "API Failure"
                    },
                  },
                }




        elif (tag=="updateTicket" or tag=="updateticket"): # update asknow ticket
          if "SymptomsCategory" in req["sessionInfo"]["parameters"]:
            symptomsCategory = req["sessionInfo"]["parameters"]["SymptomsCategory"]
          else:
            symptomsCategory=""
          if "Application" in req["sessionInfo"]["parameters"]:
            application = req["sessionInfo"]["parameters"]["Application"]
          else:
            application=""
          if "Categorization" in req["sessionInfo"]["parameters"]:
            categorization = req["sessionInfo"]["parameters"]["Categorization"]
          else:
            categorization=""
          if "ResolutionCategory" in req["sessionInfo"]["parameters"]:
            resolutionCategory = req["sessionInfo"]["parameters"]["ResolutionCategory"]
          else:
            resolutionCategory=""
          headers = {'Authorization': Asknow_Auth}
          payload = {
                 "cmdb_ci": req["sessionInfo"]["parameters"]["bsSysID"],
                 "u_symptoms_category" :symptomsCategory,
                 #"work_notes": "History",
                 "u_application": application,
                 "u_categorization": categorization,
                "u_resolution_category": resolutionCategory
              }
          updateIncidentResponse = requests.request("PUT", Asknow_url+"/api/now/table/incident/"+req["sessionInfo"]["parameters"]["ticketSysID"], headers=headers,json=payload)
          if updateIncidentResponse.status_code==200:
              updateIncidentResponsetext= json.loads(updateIncidentResponse.text)
              if updateIncidentResponsetext["result"]:
                res = {
                 "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Ticket Updated",
                    },
                  },
                }
              else:
                res = {
                 "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Not Updated"
                    },
                  },
                }
          else:
              res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "API Failure"
                    },
                  },
                }



        elif (tag=="resolveTicket" or tag=="resolveticket"): # resolve asknow ticket

          if "symptomsCategory" in req["sessionInfo"]["parameters"]:
            symptomsCategory = req["sessionInfo"]["parameters"]["symptomsCategory"]
          else:
            symptomsCategory=""

          if "application" in req["sessionInfo"]["parameters"]:
            application = req["sessionInfo"]["parameters"]["application"]
          else:
            application=""

          if "categorization" in req["sessionInfo"]["parameters"]:
            categorization = req["sessionInfo"]["parameters"]["categorization"]
          else:
            categorization=""

          if "resolutionCategory" in req["sessionInfo"]["parameters"]:
            resolutionCategory = req["sessionInfo"]["parameters"]["resolutionCategory"]
          else:
            resolutionCategory=""

          if "closeNotes" in req["sessionInfo"]["parameters"]:
            closeNotes = req["sessionInfo"]["parameters"]["closeNotes"]
          else:
            closeNotes="Automated Resolution"

          headers = {'Authorization': Asknow_Auth}
          payload = {
                   "assigned_to" : "Automation Ayehu",
                   "close_code": "Closed (Successfully)",
                   "close_notes": closeNotes,
                   "u_symptoms_category" :symptomsCategory,
                   "u_application": application,
                   "u_categorization": categorization,
                   "u_resolution_category": resolutionCategory,
                   "state": "6" ,
                   "incident_state": "6"
              }
          resolveIncidentResponse = requests.request("PUT", Asknow_url+"/api/now/table/incident/"+req["sessionInfo"]["parameters"]["ticketSysID"], headers=headers,json=payload)
          if resolveIncidentResponse.status_code==200:
              resolveIncidentResponsetext= json.loads(resolveIncidentResponse.text)
              if resolveIncidentResponsetext["result"]:
                res = {
                 "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Ticket Resolved",
                    },
                  },
                }
              else:
                res = {
                 "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "Not Resolved"
                    },
                  },
                }
          else:
              res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "API Failure"
                    },
                  },
                }



        elif (tag=="getQueueID" or tag=="getqueueid"): # get queue id ofor ccai
          skill = req["sessionInfo"]["parameters"]["escalationSkill"]
          queueid = escalation_skill[skill]
          res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "QueueID": queueid
                    }
                 }
               }
        

        elif (tag=="getmanageremail" or tag=="getManagerEmail"):   #get manager email id
            oracle_id = req["sessionInfo"]["parameters"]["oracle_id"]
            headers = {'Authorization': Asknow_Auth}
            GetManagerResponse = requests.request("GET", Asknow_url+"/api/now/table/sys_user?sysparm_query=employee_number="+oracle_id+"^active=true^user_nameISNOTEMPTY&sysparm_fields=sys_id, u_imported_location,location,manager.name,name,manager.email,active,u_business_service&sysparm_limit=1&sysparm_exclude_reference_link=true", headers=headers)
            if GetManagerResponse.status_code==200:
              GetManagerResponsetext= json.loads(GetManagerResponse.text)
              if GetManagerResponsetext["result"]:
                res = {
                  "sessionInfo": {
                     "parameters": {
                       "Webhook_Error": "false",
                       "Response_Value": "ID Found",
                       "userSysID":GetManagerResponsetext["result"][0]["sys_id"],
                       "managerEmail":GetManagerResponsetext["result"][0]["manager.email"],
                       "managerName":GetManagerResponsetext["result"][0]["manager.name"],
                       "servicenowUserName":GetManagerResponsetext["result"][0]["name"]
                    },
                  },
                }
              else:
                res = {
                  "sessionInfo": {
                     "parameters": {
                       "Webhook_Error": "false",
                       "Response_Value": "ID not found"
                    },
                  },
                }
            else:
              res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "false",
                    "Response_Value": "API Failure"
                    },
                  },
                }


        elif (tag=="sendemail" or tag=="sendEmail"): # send manager email
          headers = {'Authorization': Email_auth}
          payload = {

                  "to": req["sessionInfo"]["parameters"]["managerEmail"],
 
                  "cc": "",

                  "subject": "Caller "+req["sessionInfo"]["parameters"]["oracle_id"]+" - Reached out to Service Desk",

                  "body": "Hello "+req["sessionInfo"]["parameters"]["managerName"]+",<br><br>We are unable to assist Employee <b>"+req["sessionInfo"]["parameters"]["servicenowUserName"]+"</b>. Our system indicates his/her AD Account has been deactivated. If this is an error, please open a reactivation ticket. <br><br><a href='https://teletechinc.sharepoint.com/:b:/r/teams/ISUBCASSOS/Others/End%20User%20Guides/How%20to%20create%20an%20IDM%20-%20Reactivation%20Ticket%20v2.pdf?csf=1&web=1&e=ynaVgu'>How to create an IDM - Reactivation Ticket v2.pdf</a><br><br>Thank you <br><br><br>"

                    }
          SendEMailResponse = requests.request("POST", Email_url, headers=headers,json=payload)
          if SendEMailResponse.status_code == 200:
            res = {
                  "sessionInfo": {
                     "parameters": {
                       "Webhook_Error": "false",
                       "Response_Value": "Email Sent"
                    },
                  },
                }
          else:
            res = {
                  "sessionInfo": {
                     "parameters": {
                       "Webhook_Error": "false",
                       "Response_Value": "Email not sent"
                    },
                  },
                }



        else:
            res = {
               "sessionInfo": {
                  "parameters": {
                    "Webhook_Error": "true",
                    "Response_Value": "Tag Not Found"
                    },
                  },
                }


        return res #response from all modules 
    except Exception as e:
        res = {
            "sessionInfo": {
                "parameters": {
                    "Webhook_Error": "true"
                },
            },
         }
        # print(e)
        # print("Exception line number:", traceback.format_exc())
        return res
        



		
request_params={
	"sessionInfo": {
		"parameters": {
			"oracle_id": "7504141",
			"oracleid": "2123973",
      "authenticated":"true",
      "userLocation":"4acb3bbe6ffb450013c1199fae3ee40d",
      "userSysID":"2114975b6fd8e58864f2cccc5d3ee482",
      "userBS":"86ba01486f742d88f7cf04b0be3ee4c2",
      "uLobSite":"aa9222cb6fec9100ac14373aea3ee491",
      "short_description":"test ticket",
      "description":"test ticket desc",
      "assignment_group":"93384c0c6f570d0013c1199fae3ee4ef",
      "userManager":"125922416fe7c1004da1677eae3ee400",
      "bsSysID":"df3e657cdb39cf0c52aa5205dc96194a",
      "ticketSysID":"ce64e211870ee11c97c8646d8bbb3584",
      "escalationSkill":"ASD Hard Stick Other",
      "managerName":"Balaji",
      "managerEmail":"balaji.yeduri@ttec.com",
      "servicenowUserName":"Priya"

		}
	},
	"fulfillmentInfo": {
		"tag": "uservalidation"
	}
}
print(ivr_apis(request_params))
#req.body.fulfillmentInfo.tag
#req.body.sessionInfo.parameters.age