from bs4 import BeautifulSoup
import config
from datetime import datetime
from enum import Enum
import gspread
import requests
import time
from gspread.exceptions import APIError


gc = gspread.service_account(filename="service_account.json")

sh = gc.open_by_url(
    "https://docs.google.com/spreadsheets/d/1TRXYoEgHvJyhbSuwsXzNhNdP3uHd4-kAZT77arCrRNc/edit?gid=0#gid=0"
)


class KennelName(Enum):
    A6 = 348
    A16 = 358
    A15 = 357
    A14 = 356
    A13 = 355
    A12 = 354
    A11 = 353
    A10 = 352
    A8 = 350
    A7 = 349
    A9 = 351
    A5 = 347
    A4 = 346
    A3 = 345
    A2 = 344
    A1 = 343
    B15 = 373
    B16 = 374
    B17 = 375
    B18 = 376
    B19 = 377
    B20 = 378
    B21 = 379
    B22 = 380
    B23 = 381
    B24 = 382
    B25 = 383
    B26 = 384
    B27 = 385
    B6 = 364
    B13 = 371
    B14 = 372
    B1 = 359
    B2 = 360
    B3 = 361
    B4 = 362
    B5 = 363
    B7 = 365
    B8 = 366
    B9 = 367
    B10 = 368
    B11 = 369
    B12 = 370
    C13 = 398
    C12 = 397
    C11 = 396
    C10 = 395
    C9 = 394
    C8 = 393
    C7 = 392
    C6 = 391
    C5 = 390
    C4 = 389
    C3 = 388
    C2 = 387
    C1 = 386
    CrateBank6 = 404
    CrateBank5 = 403
    CrateBank4 = 402
    CrateBank3 = 401
    CrateBank2 = 400
    CrateBank1 = 399
    Crate2 = 265
    Crate1 = 264
    Crate20 = 414
    Crate19 = 413
    Crate18 = 412
    Crate17 = 411
    Crate16 = 410
    Crate15 = 409
    Crate14 = 408
    Crate13 = 407
    Crate12 = 406
    Crate10 = 320
    Crate3 = 266
    Crate4 = 267
    Crate5 = 268
    Crate6 = 316
    Crate7 = 317
    Crate8 = 318
    Crate9 = 319
    Crate11 = 405


today = datetime.now().strftime("%Y-%m-%d")


login_url = "https://dogsdowntownva.gingrapp.com/auth/login"
run_url = "https://dogsdowntownva.gingrapp.com//locations/get_areas?location=1"
lodging_url = "https://dogsdowntownva.gingrapp.com/calendar/lodging_calendar"
lodgingdata_url = (
    "https://dogsdowntownva.gingrapp.com/runs/get_runs_reservations?location=1&startDate="
    + today
    + "&endDate="
    + today
)


# get CSRF token and login
def gingrLogin(session):
    response = session.get(login_url)
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_token = soup.find("input", {"name": "gingr_csrf_token"})["value"]
    payload = {
        "gingr_csrf_token": csrf_token,
        "identity": config.gingrEmail,
        "password": config.gingrPassword,
    }
    response = session.post(login_url, data=payload)

    # Confirm Login was successful
    soup = BeautifulSoup(response.text, "html.parser")
    if "Dashboard" in soup.title.string:
        print("Login successful")

    return session


def getCheckedInReservations():
    url = "https://dogsdowntownva.gingrapp.com/api/v1/reservations?key=d46009d4a621dd8d4cd4dfdbe9d27f19&checked_in=true"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"key": "d46009d4a621dd8d4cd4dfdbe9d27f19", "checked_in": "true"}
    response = requests.post(url, headers=headers, data=data).json()
    checkedInReservationIDs = []
    for k in response["data"]:
        checkedInReservationIDs.append(k)

    return checkedInReservationIDs


def GetLodgingData(session):
    response = session.get(lodgingdata_url)
    data = response.json()
    lodgingDictList = []
    validReservations = getCheckedInReservations()
    for run in data:
        if run != "occupancy":
            dogs = []
            for reservation in data[run][today]:

                if reservation["reservation_id"] in validReservations:
                    dogs.append(
                        reservation["animal_name"]
                        + " "
                        + reservation["owner_last_name"]
                    )
            lodgingDictList.append(
                {"Kennel_Name": str(KennelName(int(run)).name), "Dogs": dogs}
            )
    return lodgingDictList


""" script to get run id and name for specific areas

runData = session.get(run_url).json()
for run in runData["5"]["runs"]:
    print("GeneralCrate" + str(run["name"])[-2:] + " = " + str(run["id"]))
s
"""


def cleanAHealthCheckEmptyDuplicates(url, sheetName="Sheet1"):
    KennelWksht = gc.open_by_url(url)
    healthCheckSh = KennelWksht.worksheet(sheetName)
    for kennel in KennelName:
        for attempt in range(20):
            try:
                if kennel.name[0] == "A":
                    allKennels = healthCheckSh.findall(
                        query=str(kennel.name), case_sensitive=False
                    )
                    for foundKennelNameCell in allKennels:
                        healthCheckSh.update_cell(
                            row=foundKennelNameCell.row,
                            col=foundKennelNameCell.col + 1,
                            value="",
                        )
                    if len(allKennels) > 1:
                        for foundKennelNameCell in allKennels[:-1]:
                            healthCheckSh.delete_rows(foundKennelNameCell.row)
            except Exception as e:
                if attempt < 5:
                    time.sleep(attempt)
                else:
                    time.sleep(5)
                print("ERROR CAUGHT AND RETRIED:", e)
            else:
                break
    print("Removed Duplicate Kennel Rows")


def cleanBHealthCheckEmptyDuplicates(url, sheetName="Sheet1"):
    KennelWksht = gc.open_by_url(url)
    healthCheckSh = KennelWksht.worksheet(sheetName)
    for kennel in KennelName:
        for attempt in range(20):
            try:
                if kennel.name[0] == "B":
                    allKennels = healthCheckSh.findall(
                        query=str(kennel.name), case_sensitive=False
                    )
                    for foundKennelNameCell in allKennels:
                        healthCheckSh.update_cell(
                            row=foundKennelNameCell.row,
                            col=foundKennelNameCell.col + 1,
                            value="",
                        )
                    if len(allKennels) > 1:
                        for foundKennelNameCell in allKennels[:-1]:
                            healthCheckSh.delete_rows(foundKennelNameCell.row)
            except Exception as e:
                if attempt < 5:
                    time.sleep(attempt)
                else:
                    time.sleep(5)
                print("ERROR CAUGHT AND RETRIED:", e)
            else:
                break

    print("Removed Duplicate Kennel Rows")


def insertKennelADogs(kennelDict, url, sheetName="Sheet1"):
    KennelWksht = gc.open_by_url(url)
    healthCheckSh = KennelWksht.worksheet(sheetName)

    cleanAHealthCheckEmptyDuplicates(url=url, sheetName=sheetName)

    for pairing in kennelDict:
        for attempt in range(20):
            try:
                if pairing["Kennel_Name"][0] == "A":
                    kennelCell = healthCheckSh.find(
                        str(pairing["Kennel_Name"]), case_sensitive=False
                    )

                    if kennelCell is not None:
                        nameCell = healthCheckSh.cell(
                            row=kennelCell.row, col=kennelCell.col + 1
                        )

                        if len(pairing["Dogs"]) > 1:
                            healthCheckSh.update_cell(
                                row=nameCell.row,
                                col=nameCell.col,
                                value=pairing["Dogs"][0],
                            )
                            for dog in pairing["Dogs"][1:]:

                                healthCheckSh.insert_row(
                                    values=[pairing["Kennel_Name"], str(dog)],
                                    index=nameCell.row,
                                )

                        elif len(pairing["Dogs"]) == 1:
                            healthCheckSh.update_cell(
                                row=nameCell.row,
                                col=nameCell.col,
                                value=pairing["Dogs"][0],
                            )
            except Exception as e:
                if attempt < 5:
                    time.sleep(attempt)
                else:
                    time.sleep(5)
                print("ERROR CAUGHT AND RETRIED:", e)
            else:
                break
    print("Successfully Completed Kennel A")


def insertKennelBDogs(kennelDict, url, sheetName="Sheet1"):
    KennelWksht = gc.open_by_url(url)
    healthCheckSh = KennelWksht.worksheet(sheetName)
    cleanBHealthCheckEmptyDuplicates(url=url, sheetName=sheetName)

    for pairing in kennelDict:
        for attempt in range(20):
            try:
                if pairing["Kennel_Name"][0] == "B":
                    kennelCell = healthCheckSh.find(
                        str(pairing["Kennel_Name"]), case_sensitive=False
                    )

                    if kennelCell is not None:
                        nameCell = healthCheckSh.cell(
                            row=kennelCell.row, col=kennelCell.col + 1
                        )

                        if len(pairing["Dogs"]) > 1:
                            healthCheckSh.update_cell(
                                row=nameCell.row,
                                col=nameCell.col,
                                value=pairing["Dogs"][0],
                            )
                            for dog in pairing["Dogs"][1:]:

                                healthCheckSh.insert_row(
                                    values=[pairing["Kennel_Name"], str(dog)],
                                    index=nameCell.row,
                                )

                        elif len(pairing["Dogs"]) == 1:
                            healthCheckSh.update_cell(
                                row=nameCell.row,
                                col=nameCell.col,
                                value=pairing["Dogs"][0],
                            )
            except Exception as e:
                if attempt < 5:
                    time.sleep(attempt)
                else:
                    time.sleep(5)
                print("ERROR CAUGHT AND RETRIED:", e)
            else:
                break
    print("Successfully Completed Kennel B")


def main():
    session = requests.Session()
    session = gingrLogin(session)
    print(GetLodgingData(session))

    insertKennelADogs(
        GetLodgingData(session), url=config.kennelAHealthCheckURL, sheetName="Sheet1"
    )
    insertKennelBDogs(
        GetLodgingData(session), url=config.kennelBHealthCheckURL, sheetName="Sheet1"
    )


if __name__ == "__main__":
    main()
