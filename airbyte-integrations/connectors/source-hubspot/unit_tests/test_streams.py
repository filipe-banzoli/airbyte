#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#

import pytest
from source_hubspot.streams import (
    Campaigns,
    Companies,
    ContactLists,
    Contacts,
    DealPipelines,
    Deals,
    EmailEvents,
    EngagementsCalls,
    EngagementsEmails,
    EngagementsMeetings,
    EngagementsNotes,
    EngagementsTasks,
    FeedbackSubmissions,
    Forms,
    FormSubmissions,
    LineItems,
    MarketingEmails,
    Owners,
    Products,
    Quotes,
    TicketPipelines,
    Tickets,
    Workflows,
)

from .utils import read_full_refresh, read_incremental


@pytest.mark.parametrize(
    "stream, endpoint",
    [
        (Campaigns, "campaigns"),
        (Companies, "company"),
        (ContactLists, "contact"),
        (Contacts, "contact"),
        (Deals, "deal"),
        (DealPipelines, "deal"),
        (Quotes, "quote"),
        (EmailEvents, ""),
        (EngagementsCalls, "calls"),
        (EngagementsEmails, "emails"),
        (EngagementsMeetings, "meetings"),
        (EngagementsNotes, "notes"),
        (EngagementsTasks, "tasks"),
        (FeedbackSubmissions, "feedback_submissions"),
        (Forms, "form"),
        (FormSubmissions, "form"),
        (LineItems, "line_item"),
        (MarketingEmails, ""),
        (Owners, ""),
        (Products, "product"),
        (Quotes, "quote"),
        (TicketPipelines, ""),
        (Tickets, "ticket"),
        (Workflows, ""),
    ],
)
def test_streams_read(stream, endpoint, requests_mock, common_params, fake_properties_list):
    stream = stream(**common_params)
    responses = [
        {
            "json": {
                stream.data_field: [
                    {
                        "id": "test_id",
                        "created": "2022-02-25T16:43:11Z",
                        "updatedAt": "2022-02-25T16:43:11Z",
                        "lastUpdatedTime": "2022-02-25T16:43:11Z",
                    }
                ],
            }
        }
    ]
    properties_response = [
        {
            "json": [
                {"name": property_name, "type": "string", "updatedAt": 1571085954360, "createdAt": 1565059306048}
                for property_name in fake_properties_list
            ],
            "status_code": 200,
        }
    ]
    is_form_submission = isinstance(stream, FormSubmissions)
    stream_url = stream.url + "/test_id" if is_form_submission else stream.url

    requests_mock.register_uri("GET", stream_url, responses)
    requests_mock.register_uri("GET", "/marketing/v3/forms", responses)
    requests_mock.register_uri("GET", "/email/public/v1/campaigns/test_id", responses)
    requests_mock.register_uri("GET", f"/properties/v2/{endpoint}/properties", properties_response)

    records = read_incremental(stream, {})

    assert records


@pytest.mark.parametrize(
    "error_response",
    [
        {"json": {}, "status_code": 429},
        {"json": {}, "status_code": 502},
        {"json": {}, "status_code": 504},
    ],
)
def test_common_error_retry(error_response, requests_mock, common_params, fake_properties_list):
    """Error once, check that we retry and not fail"""
    properties_response = [
        {"name": property_name, "type": "string", "updatedAt": 1571085954360, "createdAt": 1565059306048}
        for property_name in fake_properties_list
    ]
    responses = [
        error_response,
        {
            "json": properties_response,
            "status_code": 200,
        },
    ]

    stream = Companies(**common_params)

    response = {
        stream.data_field: [
            {
                "id": "test_id",
                "created": "2022-02-25T16:43:11Z",
                "updatedAt": "2022-02-25T16:43:11Z",
                "lastUpdatedTime": "2022-02-25T16:43:11Z",
            }
        ],
    }
    requests_mock.register_uri("GET", "/properties/v2/company/properties", responses)
    requests_mock.register_uri("GET", stream.url, [{"json": response}])
    records = read_full_refresh(stream)

    assert [response[stream.data_field][0]] == records
