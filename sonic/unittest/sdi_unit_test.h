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

/*
 * filename: sdi_unit_test.h
 */



#ifndef SDI_UNIT_TEST_H
#define SDI_UNIT_TEST_H


#include "sdi_entity.h"
#include "std_config_node.h"
#include "stdlib.h"
#include <vector>
#include <string>

/**
 * @defgroup sdi_ut_sys SDI Unit Test
 * SDI Unit test uses two set of views.
 * \n a. SdiReferenceImplementation describes the expected entities and the
 * resources contained in each of the entity along with other information
 * from the config file.
 * \n b. SdiTargetImplementation that is discovered at runtime obtains
 * information of entity and its resources using the SDI APIs.
 * \n The views are then used to derive various test-cases as needed for the
 * unit test.
 *
 *
 * @{
 */

/**
 * @}
 */

/**
 * @ingroup sdi_ut_entity
 * @{
 *
 * @defgroup sdi_ut_resource SdiResource
 * It has information generic to Target and Reference resources.
 *
 * @{
 */
class SdiResource {
    public:
        /** Type of the resource. */
        sdi_resource_type_t resource_type;
        /** Name of the resource. */
        std::string resource_alias_name;
};
/**
 * @}
 */

/**
 * @}
 */

/**
 * @ingroup sdi_target
 * @{
 * @brief SdiTargetResource contains the details of all the target resources.
 *
 */
class SdiTargetResource:public SdiResource
{
    public:
        /**
         * The constructor uses the resource handle associated with SDI APIs to get the
         * specific information of a resource.
         */
        SdiTargetResource(sdi_resource_hdl_t res_hdl);
};
/**
 * @}
 */

/**
 * @ingroup sdi_reference
 * @{
 * @brief SdiReferenceResource contains the details of reference resources.
 */
class SdiReferenceResource:public SdiResource
{
    public:
        /**
         * The constructor uses the resource node in config file to get the information of a
         * resource.
         */
        SdiReferenceResource(std_config_node_t resource_node);
        /**
         * Validates information received from target and reference resources.
         * @param  target - a reference to SdiTargetResource object.
         * @return true if the resource alias name and resource type of resources in the target and reference
         * are equal.*/
        bool isValidResourceImplementation(SdiTargetResource &target);
};
/**
 * @}
 */

/**
 * @ingroup sdi_ut_resource
 * @{
 * @brief SdiFanResource has information generic to a fan.
 * @todo APIs to get details of fan speed.
 *
 */
class SdiFanResource: public SdiResource {
    public:
        /** Max Speed of Fan in RPM. */
        uint_t max_speed;
};
/**
 * @}
 */

/**
 * @ingroup sdi_target
 * @{
 * @brief SdiTargetFanResource contains the details of all the fan resources from the
 * Target.
 */
class SdiTargetFanResource: public SdiFanResource,public SdiTargetResource{
    public:
        /**
         * The constructor uses the resource handle which is associated with specific SDI APIs to get details of fan.
         */
        SdiTargetFanResource(sdi_resource_hdl_t res_hdl);
        /** Gets speed of Fan. */
        uint_t speed_get(sdi_resource_hdl_t res_hdl);
    private:
        /** An opaque handle to an
         * resource which is used to retrieve the specific details of Fan.*/
        sdi_resource_hdl_t hdl;
};
/**
 * @}
 */

/**
 * @ingroup sdi_ut_sys
 * @{
 * @defgroup sdi_ut_entity SDI Entity
 * It consists of list of resources and generic information used by
 * target and reference, through which each entity can be identified.
 *
 * @{
 *
 */
class SdiEntity {
    public:
        /** Name of entity. */
        std::string entity_name;
        /** Type of the entity.*/
        sdi_entity_type_t entity_type;
};
/**
 * @}
 */

/**
 * @}
 */

/**
 * @ingroup sdi_target
 * @{
 * @brief SdiTargetEntity contains the details of all the target entities.
 */
class SdiTargetEntity:public SdiEntity {
    public:
        /**
         * The constructor uses the entity handle which is associated with certain SDI APIs to get
         * information of an entity.
         */
        SdiTargetEntity(sdi_entity_hdl_t hdl);
        /** List of entities in Target. */
        std::vector <SdiTargetResource *> target_resource;
    private:
        /** An opaque handle to an entity,which is used for retrieving the
         * resource hdl.*/
        sdi_entity_hdl_t hdl;
};
/**
 * @}
 */

/**
 * @ingroup sdi_reference
 * @{
 * @brief SdiReferenceEntity contains the details of all the reference entities.
 *
 */
class SdiReferenceEntity:public SdiEntity {
    public:
        /**
         * The constructor uses the entity node in the config file to obtain
         * the information of an entity.
         */
        SdiReferenceEntity(std_config_node_t node);
        /**
         * Validates information received from target and reference resources.
         * @param  target - a reference to SdiTargetEntity object.
         * @return true if the entity alias name and entity type of entities in the target and reference
         *  are equal.
         */
        bool isValidEntityImplementation(SdiTargetEntity &target);
        /** It is the resource type, acquired from reference which used to
         *  check the type of resource.*/
        sdi_resource_type_t  res_type;
        /** List of entities in reference. */
        std::vector <SdiReferenceResource *> reference_resource;
};
/**
 * @}
 */

/**
 * @ingroup sdi_ut_sys
 * @{
 * SDI Unit Test Implemenation consists of two major classes for performing unit test.
 * SdiTargetEntity gets the information of every entity in DUT using SDI APIs.
 * SdiReferenceEntity gets the information of every entity in DUT from its config file.
 *
 */


/**
 * @}
 */

/**
 * @ingroup sdi_ut_sys
 * @{
 * @defgroup sdi_target SdiTargetImplementation
 * It populates the required information from target into target entity list.
 *
 * @{
 */
class SdiTargetImplementation{
    public:
        /**
         * Based on number of entities, it populates the target entity list by
         * using SDI APIs.
         */
        SdiTargetImplementation();
        /** List of entities in Target.*/
        std::vector <SdiTargetEntity *> target_entity;
    private:
        /** Maximum number of entities.*/
        uint_t  max_entities;
        /** Type of the entity. */
        uint_t entity_type;
        /** Instance of the entity. */
        uint_t entity_id;
        /** An opaque handle to an entity, used to retrieve the specific
         * details of an entity. */
        sdi_entity_hdl_t hdl;
};

/**
 * @}
 */

/**
 * @}
 */

/**
 * @ingroup sdi_ut_sys
 * @{
 * @defgroup sdi_reference SdiReferenceImplementation
 * It populates the required information from reference into reference entity list.
 *
 * @{
 */
class SdiReferenceImplementation {
    public:
        /**
         * Traverses the config file and populates the reference entity list
         * accordingly.
         */
        SdiReferenceImplementation();
        /**
         * Validates information received from target and reference entity lists.
         * @param  target a reference to SdiTargetImplementation object.
         * @return true if the contents in the target and reference entity lists
         * are equal.*/
        bool isValidImplementation(SdiTargetImplementation &target);
        /** List of entities in Reference.*/
        std::vector <SdiReferenceEntity *> reference_entity;
};
/**
 * @}
 */

/**
 * @}
 */

#endif  //SDI_UNIT_TEST_H
