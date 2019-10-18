from NVMeshSDK.APIs.UserAPI import UserAPI
from NVMeshSDK.Entities.User import User

import TestBaseClass

import unittest


class UserTest(TestBaseClass.TestBaseClass):

    def getEntitiesForSave(self):
        return [
            User(email="test1@tester.com", role="Admin", notificationLevel="NONE", password="test"),
            User(email="test2@tester.com", role="Observer", notificationLevel="NONE", password="testitest")
        ]

    def getEntitiesForUpdateAndDelete(self):
        return [
            User(
                _id="testdel@tester.com",
                role="Observer",
                notificationLevel="NONE",
                email="testdel@tester.com",
                modifiedBy="admin@excelero.com",
                createdBy="admin@excelero.com",
                dateModified="2019-04-01T13:54:30.875Z",
                dateCreated="2019-04-01T13:54:30.875Z",
                layout={
                    "statistics": {
                        "elements": [
                            {
                                "top": 450,
                                "left": 0,
                                "width": 300,
                                "height": 150,
                                "minHeight": 150,
                                "minWidth": 300,
                                "type": "spark-line",
                                "options": {
                                    "selectedFields": [
                                        {
                                            "entityType": "CLUSTER",
                                            "filter": "nvmesh",
                                            "category": "total",
                                            "counterGroup": "size",
                                            "thing": "read"
                                        }
                                    ],
                                    "title": "Cluster Reads",
                                    "selection": {
                                        "entities": [
                                            {
                                                "type": "CLUSTER",
                                                "id": "nvmesh"
                                            }
                                        ]
                                    },
                                    "titleMode": "custom"
                                }
                            },
                            {
                                "top": 300,
                                "left": 0,
                                "width": 300,
                                "height": 150,
                                "minHeight": 150,
                                "minWidth": 300,
                                "type": "spark-line",
                                "options": {
                                    "selectedFields": [
                                        {
                                            "entityType": "CLUSTER",
                                            "filter": "nvmesh",
                                            "category": "total",
                                            "counterGroup": "size",
                                            "thing": "write"
                                        }
                                    ],
                                    "title": "Cluster Writes",
                                    "selection": {
                                        "entities": [
                                            {
                                                "type": "CLUSTER",
                                                "id": "nvmesh"
                                            }
                                        ]
                                    },
                                    "titleMode": "custom"
                                }
                            },
                            {
                                "top": 0,
                                "left": 0,
                                "width": 300,
                                "height": 300,
                                "minHeight": 300,
                                "minWidth": 300,
                                "type": "dial-gauge",
                                "options": {
                                    "selectedFields": [
                                        {
                                            "entityType": "CLUSTER",
                                            "filter": "nvmesh",
                                            "category": "total",
                                            "counterGroup": "size",
                                            "thing": "read"
                                        },
                                        {
                                            "entityType": "CLUSTER",
                                            "filter": "nvmesh",
                                            "category": "total",
                                            "counterGroup": "size",
                                            "thing": "write"
                                        }
                                    ],
                                    "title": "Total Throughput",
                                    "maxValue": 0,
                                    "autoMax": True,
                                    "selection": {
                                        "entities": [
                                            {
                                                "type": "CLUSTER",
                                                "id": "nvmesh"
                                            }
                                        ]
                                    }
                                }
                            },
                            {
                                "top": 0,
                                "left": 300,
                                "width": 600,
                                "height": 300,
                                "minHeight": 300,
                                "minWidth": 300,
                                "type": "line-chart",
                                "options": {
                                    "selectedFields": [
                                        {
                                            "entityType": "CLUSTER",
                                            "filter": "nvmesh",
                                            "category": "total",
                                            "counterGroup": "ops",
                                            "thing": "read"
                                        },
                                        {
                                            "entityType": "CLUSTER",
                                            "filter": "nvmesh",
                                            "category": "total",
                                            "counterGroup": "ops",
                                            "thing": "write"
                                        },
                                        {
                                            "entityType": "CLUSTER",
                                            "filter": "nvmesh",
                                            "category": "total",
                                            "counterGroup": "ops",
                                            "thing": "trim"
                                        }
                                    ],
                                    "title": "Cluster IOPs",
                                    "selection": {
                                        "entities": [
                                            {
                                                "type": "CLUSTER",
                                                "id": "nvmesh"
                                            }
                                        ]
                                    }
                                }
                            },
                            {
                                "top": 0,
                                "left": 900,
                                "width": 650,
                                "height": 300,
                                "minHeight": 300,
                                "minWidth": 300,
                                "type": "line-chart",
                                "options": {
                                    "selectedFields": [
                                        {
                                            "entityType": "CLUSTER",
                                            "filter": "nvmesh",
                                            "category": "total",
                                            "counterGroup": "size",
                                            "thing": "read"
                                        },
                                        {
                                            "entityType": "CLUSTER",
                                            "filter": "nvmesh",
                                            "category": "total",
                                            "counterGroup": "size",
                                            "thing": "write"
                                        },
                                        {
                                            "entityType": "CLUSTER",
                                            "filter": "nvmesh",
                                            "category": "total",
                                            "counterGroup": "size",
                                            "thing": "trim"
                                        }
                                    ],
                                    "title": "Cluster Throughput",
                                    "selection": {
                                        "entities": [
                                            {
                                                "type": "CLUSTER",
                                                "id": "nvmesh"
                                            }
                                        ]
                                    },
                                    "titleMode": "custom"
                                }
                            },
                            {
                                "top": 300,
                                "left": 300,
                                "width": 600,
                                "height": 300,
                                "minHeight": 300,
                                "minWidth": 400,
                                "type": "bar-chart",
                                "options": {
                                    "selectedFields": [
                                        {
                                            "entityType": "VOLUME",
                                            "filter": "All",
                                            "category": "total",
                                            "counterGroup": "size",
                                            "thing": "read"
                                        },
                                        {
                                            "entityType": "VOLUME",
                                            "filter": "All",
                                            "category": "total",
                                            "counterGroup": "size",
                                            "thing": "write"
                                        }
                                    ],
                                    "title": "Most Active Volumes",
                                    "maxNumOfRows": 5,
                                    "selection": {
                                        "entities": [
                                            {
                                                "type": "VOLUME",
                                                "id": "All"
                                            }
                                        ]
                                    }
                                }
                            },
                            {
                                "top": 300,
                                "left": 900,
                                "width": 650,
                                "height": 300,
                                "minHeight": 300,
                                "minWidth": 400,
                                "type": "bar-chart",
                                "options": {
                                    "selectedFields": [
                                        {
                                            "entityType": "CLIENT",
                                            "filter": "All",
                                            "category": "total",
                                            "counterGroup": "size",
                                            "thing": "read"
                                        },
                                        {
                                            "entityType": "CLIENT",
                                            "filter": "All",
                                            "category": "total",
                                            "counterGroup": "size",
                                            "thing": "write"
                                        }
                                    ],
                                    "title": "Most Active Clients",
                                    "maxNumOfRows": 5,
                                    "selection": {
                                        "entities": [
                                            {
                                                "type": "CLIENT",
                                                "id": "All"
                                            }
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                }

            )
        ]

    def getDbEntities(self):
        return self.getEntitiesForUpdateAndDelete() + [
            User(
                    _id="admin@excelero.com",
                    dateCreated="2019-03-26T15:55:11.909Z",
                    email="admin@excelero.com",
                    eulaDateOfSignature="2019-03-26T16:09:54.166Z",
                    eulaSignature="klk",
                    hasAcceptedEula=True,
                    layout={
                        "statistics": {
                            "elements": [
                                {
                                    "height": 150,
                                    "left": 0,
                                    "minHeight": 150,
                                    "minWidth": 300,
                                    "options": {
                                        "selectedFields": [
                                            {
                                                "category": "total",
                                                "counterGroup": "size",
                                                "entityType": "CLUSTER",
                                                "filter": "nvmesh",
                                                "thing": "read"
                                            }
                                        ],
                                        "selection": {
                                            "entities": [
                                                {
                                                    "id": "nvmesh",
                                                    "type": "CLUSTER"
                                                }
                                            ]
                                        },
                                        "title": "Cluster Reads",
                                        "titleMode": "custom"
                                    },
                                    "top": 450,
                                    "type": "spark-line",
                                    "width": 300
                                },
                                {
                                    "height": 150,
                                    "left": 0,
                                    "minHeight": 150,
                                    "minWidth": 300,
                                    "options": {
                                        "selectedFields": [
                                            {
                                                "category": "total",
                                                "counterGroup": "size",
                                                "entityType": "CLUSTER",
                                                "filter": "nvmesh",
                                                "thing": "write"
                                            }
                                        ],
                                        "selection": {
                                            "entities": [
                                                {
                                                    "id": "nvmesh",
                                                    "type": "CLUSTER"
                                                }
                                            ]
                                        },
                                        "title": "Cluster Writes",
                                        "titleMode": "custom"
                                    },
                                    "top": 300,
                                    "type": "spark-line",
                                    "width": 300
                                },
                                {
                                    "height": 300,
                                    "left": 0,
                                    "minHeight": 300,
                                    "minWidth": 300,
                                    "options": {
                                        "autoMax": True,
                                        "maxValue": 0,
                                        "selectedFields": [
                                            {
                                                "category": "total",
                                                "counterGroup": "size",
                                                "entityType": "CLUSTER",
                                                "filter": "nvmesh",
                                                "thing": "read"
                                            },
                                            {
                                                "category": "total",
                                                "counterGroup": "size",
                                                "entityType": "CLUSTER",
                                                "filter": "nvmesh",
                                                "thing": "write"
                                            }
                                        ],
                                        "selection": {
                                            "entities": [
                                                {
                                                    "id": "nvmesh",
                                                    "type": "CLUSTER"
                                                }
                                            ]
                                        },
                                        "title": "Total Throughput"
                                    },
                                    "top": 0,
                                    "type": "dial-gauge",
                                    "width": 300
                                },
                                {
                                    "height": 300,
                                    "left": 300,
                                    "minHeight": 300,
                                    "minWidth": 300,
                                    "options": {
                                        "selectedFields": [
                                            {
                                                "category": "total",
                                                "counterGroup": "ops",
                                                "entityType": "CLUSTER",
                                                "filter": "nvmesh",
                                                "thing": "read"
                                            },
                                            {
                                                "category": "total",
                                                "counterGroup": "ops",
                                                "entityType": "CLUSTER",
                                                "filter": "nvmesh",
                                                "thing": "write"
                                            },
                                            {
                                                "category": "total",
                                                "counterGroup": "ops",
                                                "entityType": "CLUSTER",
                                                "filter": "nvmesh",
                                                "thing": "trim"
                                            }
                                        ],
                                        "selection": {
                                            "entities": [
                                                {
                                                    "id": "nvmesh",
                                                    "type": "CLUSTER"
                                                }
                                            ]
                                        },
                                        "title": "Cluster IOPs"
                                    },
                                    "top": 0,
                                    "type": "line-chart",
                                    "width": 600
                                },
                                {
                                    "height": 300,
                                    "left": 900,
                                    "minHeight": 300,
                                    "minWidth": 300,
                                    "options": {
                                        "selectedFields": [
                                            {
                                                "category": "total",
                                                "counterGroup": "size",
                                                "entityType": "CLUSTER",
                                                "filter": "nvmesh",
                                                "thing": "read"
                                            },
                                            {
                                                "category": "total",
                                                "counterGroup": "size",
                                                "entityType": "CLUSTER",
                                                "filter": "nvmesh",
                                                "thing": "write"
                                            },
                                            {
                                                "category": "total",
                                                "counterGroup": "size",
                                                "entityType": "CLUSTER",
                                                "filter": "nvmesh",
                                                "thing": "trim"
                                            }
                                        ],
                                        "selection": {
                                            "entities": [
                                                {
                                                    "id": "nvmesh",
                                                    "type": "CLUSTER"
                                                }
                                            ]
                                        },
                                        "title": "Cluster Throughput",
                                        "titleMode": "custom"
                                    },
                                    "top": 0,
                                    "type": "line-chart",
                                    "width": 650
                                },
                                {
                                    "height": 300,
                                    "left": 300,
                                    "minHeight": 300,
                                    "minWidth": 400,
                                    "options": {
                                        "maxNumOfRows": 5,
                                        "selectedFields": [
                                            {
                                                "category": "total",
                                                "counterGroup": "size",
                                                "entityType": "VOLUME",
                                                "filter": "All",
                                                "thing": "read"
                                            },
                                            {
                                                "category": "total",
                                                "counterGroup": "size",
                                                "entityType": "VOLUME",
                                                "filter": "All",
                                                "thing": "write"
                                            }
                                        ],
                                        "selection": {
                                            "entities": [
                                                {
                                                    "id": "All",
                                                    "type": "VOLUME"
                                                }
                                            ]
                                        },
                                        "title": "Most Active Volumes"
                                    },
                                    "top": 300,
                                    "type": "bar-chart",
                                    "width": 600
                                },
                                {
                                    "height": 300,
                                    "left": 900,
                                    "minHeight": 300,
                                    "minWidth": 400,
                                    "options": {
                                        "maxNumOfRows": 5,
                                        "selectedFields": [
                                            {
                                                "category": "total",
                                                "counterGroup": "size",
                                                "entityType": "CLIENT",
                                                "filter": "All",
                                                "thing": "read"
                                            },
                                            {
                                                "category": "total",
                                                "counterGroup": "size",
                                                "entityType": "CLIENT",
                                                "filter": "All",
                                                "thing": "write"
                                            }
                                        ],
                                        "selection": {
                                            "entities": [
                                                {
                                                    "id": "All",
                                                    "type": "CLIENT"
                                                }
                                            ]
                                        },
                                        "title": "Most Active Clients"
                                    },
                                    "top": 300,
                                    "type": "bar-chart",
                                    "width": 650
                                }
                            ],
                            "settings": {
                                "isControlPanelPinned": False
                            }
                        }
                    },
                    notificationLevel="NONE",
                    relogin=False,
                    role="Admin"
            )
        ]

    def testDelete(self):
        expectedRes = self.getExpectedResultObj(entities=self.getEntitiesForUpdateAndDelete())
        err, apiRes = self.myAPI.delete(self.getEntitiesForUpdateAndDelete())
        self.checkResults(expectedRes, err, apiRes)

    def test10Update(self):
        expectedRes = self.getExpectedResultObj(entities=self.getEntitiesForUpdateAndDelete())
        err, apiRes = self.myAPI.update(self.getApiUpdatePayload())
        self.checkResults(expectedRes, err, apiRes)

    def getApiUpdatePayload(self):
        users = self.getEntitiesForUpdateAndDelete()
        [setattr(user, 'role', 'Admin') for user in users]
        return users

    def test01ResetPassword(self):
        expectedRes = self.getExpectedResultObj(entities=self.getEntitiesForUpdateAndDelete(), payload={'newPassword': 'a'})
        err, apiRes = self.myAPI.resetPassword(self.getApiUpdatePayload())

        if err is None:
            for result in apiRes:
                result['payload']['newPassword'] = 'a'

        self.checkResults(expectedRes, err, apiRes)

    @staticmethod
    def getAPI():
        return UserAPI()


if __name__ == '__main__':
    unittest.main(verbosity=2)
