
/*
 * Copyright (c) 2016 Dell Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
 *
 * THIS CODE IS PROVIDED ON AN  *AS IS* BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
 *  LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
 * FOR A PARTICULAR PURPOSE, MERCHANTABLITY OR NON-INFRINGEMENT.
 *
 * See the Apache Version 2.0 License for specific language governing
 * permissions and limitations under the License.
 */


/* OPENSOURCELICENSE */

/**
 * @brief This file contains the google unit test cases to test the
 * entities and resources of a specific device.
 */
#include "unittest/sdi_unit_test.h"
#include "gtest/gtest.h"

/**
 * Tests that every entity expected by the Reference Implementation exists in the Target Implementation.
 * An Entity in Target is considered to be same as Reference, if the alias name and type are same, and if they have the same resources contained within them.
 * A Resource in Target is considered to be same as Reference, if the alias name and type are same.
 */
TEST(SdiTest, list_names)
{
     SdiTargetImplementation target;
     SdiReferenceImplementation reference;
     ASSERT_TRUE(reference.isValidImplementation(target)!=false);
}

int main(int argc, char **argv) {
    sdi_sys_init();
    ::testing::InitGoogleTest(&argc, argv);
     return RUN_ALL_TESTS();
}
