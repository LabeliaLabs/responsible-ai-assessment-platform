from django.test import TestCase

from home.models import User, Organisation, Membership, PendingInvitation, PlatformManagement
from assessment.models import Assessment, Evaluation
from assessment.tests.object_creation import create_assessment_body, create_evaluation, create_scoring


class UserTestCase(TestCase):
    def setUp(self):
        self.user_admin = User.object.create_superuser(email="admin@test.com", password="test12345")
        self.user_staff = User.object.create_staffuser(email="staff@test.com", password="test12345")
        self.user = User.object.create_user(email="user@test.com", password="test12345")

    def test_user_creation(self):
        self.assertEqual(len(list(User.object.all())), 3)

    def test_user_name(self):
        self.assertEqual(self.user.get_email(), "user@test.com")
        self.assertEqual(self.user_admin.get_short_name(), "admin@test.com")
        self.assertEqual(str(self.user_staff), "staff@test.com")

    def test_user_rights(self):
        self.assertTrue(self.user_admin.has_perm(perm=""))
        self.assertFalse(self.user.has_perm(perm=""))
        self.assertFalse(self.user_staff.has_perm(perm=""))

    def test_user_properties(self):
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_admin)
        self.assertFalse(self.user.is_staff)
        self.assertTrue(self.user_staff.is_staff)
        self.assertFalse(self.user_staff.is_admin)
        self.assertTrue(self.user_admin.is_staff)
        self.assertTrue(self.user_admin.is_admin)

    def test_user_set_name(self):
        self.user.first_name = "Jean"
        self.user.last_name = "Pierre"
        self.user.save()
        self.assertEqual(self.user.get_full_name(), "Jean Pierre")

    def test_user_deletion(self):
        self.user.delete()
        with self.assertRaises(Exception):
            User.object.get(email="user@test.com")


class OrganisationTestCase(TestCase):
    def setUp(self):
        self.user = User.object.create_user(email="user@test.com", password="test12345")

    def test_organisation_creation(self):
        organisation = Organisation.create_organisation(name="Orga_test",
                                                        size=Organisation.SIZE[0][0],
                                                        country="FR",
                                                        sector=Organisation.SECTOR[0][0],
                                                        created_by=self.user)
        self.assertIn(organisation, Organisation.objects.all())
        self.assertEqual(str(organisation), "Orga_test")
        # Test membership created
        self.assertTrue(list(Membership.objects.all()))
        membership = Membership.objects.get(organisation=organisation)
        self.assertEqual(organisation.get_list_members_not_staff(), [membership])

    def test_organisation_deletion(self):
        organisation = Organisation.create_organisation(name="Orga_test",
                                                        size=Organisation.SIZE[0][0],
                                                        country="FR",
                                                        sector=Organisation.SECTOR[0][0],
                                                        created_by=self.user)
        self.assertIn(organisation, Organisation.objects.all())
        organisation.delete()
        with self.assertRaises(Exception):
            Organisation.objects.get(name="Orga_test")


class MembershipTest(TestCase):
    def test_membership_roles(self):
        self.assertTrue(Membership.check_role("admin"))
        self.assertTrue(Membership.check_role("read_only"))
        self.assertTrue(Membership.check_role("editor"))

    def test_membership_roles_rejected(self):
        self.assertFalse(Membership.check_role("marchand de sable"))
        self.assertFalse(Membership.check_role("lecteur"))  # The French version is refused!


class OrganisationMembershipTestCAse(TestCase):
    def setUp(self):
        self.user1 = User.object.create_user(email="user1@test.com", password="test12345")
        self.user2 = User.object.create_user(email="user2@test.com", password="test12345")
        self.user3 = User.object.create_user(email="user3@test.com", password="test12345")
        self.user_admin = User.object.create_superuser(email="user@test.com", password="test12345")
        self.organisation = Organisation.create_organisation(name="Orga_test",
                                                             size=Organisation.SIZE[0][0],
                                                             country="FR",
                                                             sector=Organisation.SECTOR[0][0],
                                                             created_by=self.user1)

    def tearDown(self):
        del self.organisation

    def test_organisation_one_member(self):
        # Test the methods of the Organisation class for the user who created the organisation
        member_user1 = self.user1.membership_set.get(organisation=self.organisation)
        self.assertEqual(self.organisation.get_list_members_not_staff(), [member_user1])
        self.assertEqual(self.organisation.get_list_members_to_display(), [member_user1])
        self.assertEqual(self.organisation.count_displayed_members(), 1)
        self.assertEqual(self.organisation.get_list_admin_members(), [member_user1])
        self.assertEqual(self.organisation.count_admin_members(), 1)
        self.assertEqual(self.organisation.get_membership_user(self.user1), member_user1)
        self.assertTrue(self.organisation.check_user_is_member(self.user1))
        self.assertTrue(self.organisation.check_user_is_member_as_admin(self.user1))
        self.assertEqual(self.organisation.get_role_user(self.user1), "admin")

    def test_user_membership(self):
        # Test if the user has membership in the organisation
        member_user1 = self.user1.membership_set.get(organisation=self.organisation)
        self.assertIn(member_user1, Membership.get_list_all_memberships_user(self.user1))
        self.assertFalse(Membership.get_list_all_memberships_user(self.user2))
        self.assertIn(
            self.organisation,
            Organisation.get_list_organisations_where_user_as_role(self.user1, role="admin")
        )
        self.assertNotIn(
            self.organisation,
            Organisation.get_list_organisations_where_user_as_role(self.user1, role="read_only")
        )
        self.assertFalse(Organisation.get_list_organisations_where_user_as_role(self.user2, role="admin"))

    def test_organisation_membership_rejected(self):
        # Security checks for users not member of the organisation
        self.assertEqual(self.organisation.get_membership_user(self.user2), None)
        self.assertFalse(self.organisation.check_user_is_member(self.user2))
        self.assertFalse(self.organisation.check_user_is_member_as_admin(self.user2))
        self.assertEqual(self.organisation.get_role_user(self.user2), None)

    def test_organisation_add_user(self):
        # Add a user to the organisation and check that the membership has been created
        member_user1 = self.user1.membership_set.get(organisation=self.organisation, user=self.user1)
        with self.assertRaises(Exception):
            self.user2.membership_set.get(organisation=self.organisation, user=self.user2)
        self.organisation.add_user_to_organisation(user=self.user2, role="read_only")
        self.assertIn(
            self.organisation,
            Organisation.get_list_organisations_where_user_as_role(self.user2, "read_only")
        )
        member_user2 = self.user2.membership_set.get(organisation=self.organisation, user=self.user2)
        self.assertEqual(self.organisation.get_list_members_not_staff(), [member_user1, member_user2])
        self.assertEqual(self.organisation.get_list_members_to_display(), [member_user1, member_user2])
        self.assertIn(member_user2, Membership.get_list_all_memberships_user(self.user2))

    def test_organisation_two_members(self):
        # Add a user to the organisation and check that the organisation methods respond well
        self.organisation.add_user_to_organisation(user=self.user2, role="read_only")
        member_user1 = self.user1.membership_set.get(organisation=self.organisation, user=self.user1)
        member_user2 = Membership.objects.get(organisation=self.organisation, user=self.user2)
        self.assertEqual(self.organisation.get_list_members_not_staff(), [member_user1, member_user2])
        self.assertEqual(self.organisation.get_list_members_to_display(), [member_user1, member_user2])
        self.assertEqual(self.organisation.count_displayed_members(), 2)
        self.assertEqual(self.organisation.get_list_admin_members(), [member_user1])
        self.assertEqual(self.organisation.count_admin_members(), 1)
        self.assertEqual(self.organisation.get_membership_user(self.user1), member_user1)
        self.assertEqual(self.organisation.get_membership_user(self.user2), member_user2)
        # Security check: is the user belonging to the organisation ?
        self.assertTrue(self.organisation.check_user_is_member(self.user1))
        self.assertTrue(self.organisation.check_user_is_member_as_admin(self.user1))
        self.assertTrue(self.organisation.check_user_is_member(self.user2))
        self.assertFalse(self.organisation.check_user_is_member_as_admin(self.user2))
        self.assertFalse(self.organisation.check_user_is_member_and_can_edit_evaluations(self.user2))  # Cannot edit
        self.assertEqual(self.organisation.get_role_user(self.user2), "read_only")

    def test_organisation_remove_user(self):
        # Test removing a simple user in an organisation with 2 users
        self.organisation.add_user_to_organisation(user=self.user2, role="read_only")
        self.assertIn(
            self.organisation,
            Organisation.get_list_organisations_where_user_as_role(self.user2, role="read_only")
        )
        self.assertTrue(self.organisation.check_user_is_member(self.user2))
        self.organisation.remove_user_to_organisation(self.user2)
        with self.assertRaises(Exception):
            self.user2.membership_set.get(organisation=self.organisation, user=self.user2)
        member_user1 = self.user1.membership_set.get(organisation=self.organisation, user=self.user1)
        self.assertEqual(self.organisation.get_list_members_not_staff(), [member_user1])
        self.assertFalse(self.organisation.check_user_is_member(self.user2))

    def test_organisation_remove_user_bis(self):
        # Test that the user is not removed when it is the last one in the organisation
        self.assertEqual(self.organisation.count_displayed_members(), 1)
        self.organisation.remove_user_to_organisation(user=self.user1)
        self.assertEqual(self.organisation.count_displayed_members(), 1)
        self.assertTrue(self.organisation.check_user_is_member_as_admin(self.user1))

    def test_organisation_add_already_member(self):
        # Test that the user is not added to the organisation because he is already a member
        self.assertEqual(self.organisation.count_displayed_members(), 1)
        self.organisation.add_user_to_organisation(user=self.user1, role="read_only")
        self.assertEqual(self.organisation.count_displayed_members(), 1)
        self.assertTrue(self.organisation.check_user_is_member_as_admin(self.user1))

    def test_organisation_deletion_and_members(self):
        self.organisation.delete()
        with self.assertRaises(Exception):
            Membership.objects.get(user=self.user1)
        self.assertFalse(Membership.get_list_all_memberships_user(self.user2))  # User1 has no longer a membership
        # Todo test the view which deletes the organisation (and create it)

    def test_admin_user_membership(self):
        # Test that admin/staff user are member of the organisation as read_only
        member_user1 = self.user1.membership_set.get(organisation=self.organisation)
        member_user_admin = Membership.objects.get(organisation=self.organisation, user=self.user_admin)
        self.assertIn(
            self.organisation,
            Organisation.get_list_organisations_where_user_as_role(self.user_admin, "read_only")
        )
        self.assertNotIn(member_user_admin, self.organisation.get_list_members_not_staff())
        self.assertEqual([member_user1], self.organisation.get_list_members_not_staff())
        self.assertEqual(self.organisation.count_displayed_members(), 1)
        self.assertEqual("read_only", self.organisation.get_role_user(self.user_admin))

    def test_editor_membership_role(self):
        # Test edit membership privilege and the method check_user_is_member_and_can_edit_evaluations
        self.organisation.add_user_to_organisation(user=self.user2, role="editor")
        self.assertEqual(self.organisation.count_displayed_members(), 2)
        self.assertEqual(self.organisation.get_role_user(self.user2), "editor")
        self.assertTrue(self.organisation.check_user_is_member_and_can_edit_evaluations(self.user2))
        self.assertTrue(self.organisation.check_user_is_member_and_can_edit_evaluations(self.user1))
        self.assertFalse(self.organisation.check_user_is_member_and_can_edit_evaluations(self.user_admin))
        self.assertFalse(self.organisation.check_user_is_member_and_can_edit_evaluations(self.user3))


class OrganisationEvaluationTestCAse(TestCase):
    def setUp(self):
        self.user1 = User.object.create_user(email="user1@test.com", password="test12345")
        self.user2 = User.object.create_user(email="user2@test.com", password="test12345")
        self.user_admin = User.object.create_superuser(email="user@test.com", password="test12345")
        self.organisation = Organisation.create_organisation(name="Orga_test",
                                                             size=Organisation.SIZE[0][0],
                                                             country="FR",
                                                             sector=Organisation.SECTOR[0][0],
                                                             created_by=self.user1)
        create_assessment_body(version="1.0")
        self.assessment = Assessment.objects.get(version="1.0")
        create_scoring(assessment=self.assessment)
        self.evaluation = create_evaluation(
            assessment=self.assessment,
            name="evaluation",
            created_by=self.user1,
            organisation=self.organisation
        )

    def test_user_create_evaluation(self):
        self.assertEqual(self.organisation.get_list_evaluations(), [self.evaluation])

    def test_organisation_assessment_last_version(self):
        create_assessment_body(version="2.5")
        assessment = Assessment.objects.get(version="2.5")
        create_scoring(assessment=assessment)
        create_evaluation(
            assessment=assessment,
            name="evaluation2",
            created_by=self.user1,
            organisation=self.organisation
        )
        self.assertIn("1.0", self.organisation.get_list_assessment_version())
        self.assertIn("2.5", self.organisation.get_list_assessment_version())
        self.assertNotIn("2.0", self.organisation.get_list_assessment_version())
        self.assertEqual(self.organisation.get_last_assessment_version(), 2.5)

    def test_organisation_suppression_and_evaluation(self):
        self.organisation.delete()
        with self.assertRaises(Exception):
            Evaluation.objects.get(name="evaluation")

    # todo check user1 has access eval page while user2 doesn t


class TestPendingInvitation(TestCase):
    def setUp(self):
        self.user1 = User.object.create_user(email="user1@test.com", password="test12345")
        self.organisation = Organisation.create_organisation(name="organisation",
                                                             size=Organisation.SIZE[0][0],
                                                             country="FR",
                                                             sector=Organisation.SECTOR[0][0],
                                                             created_by=self.user1)

    def test_create_pending_invitation(self):
        """
        Test the creation of pending invitation in a case which should work and the methods associated
        """
        PendingInvitation.create_pending_invitation(email="bonjour@hotmail.com",
                                                    organisation=self.organisation,
                                                    role=Membership.ROLES[0][0]
                                                    )
        self.assertEqual(len(list(PendingInvitation.objects.all())), 1)
        invitation = PendingInvitation.objects.get(email="bonjour@hotmail.com")
        self.assertEqual(invitation.organisation, self.organisation)
        self.assertEqual(PendingInvitation.get_organisation_pending_list(self.organisation), [invitation])
        user2 = User.object.create_user(email="bonjour@hotmail.com", password="test12345")
        self.assertEqual(PendingInvitation.get_list_pending_invitation(user2), [invitation])

    def test_pending_evaluation_wrong_cases(self):
        """
        Test cases which should lead to errors because bad inputs, values
        Note that the "email" field is not checked as this has no incidence because it is a Charfield
        :return:
        """
        # Bad role string
        PendingInvitation.create_pending_invitation(email="bonjour@hotmail.com",
                                                    organisation=self.organisation,
                                                    role="escroc"
                                                    )
        with self.assertRaises(Exception):
            PendingInvitation.objects.get(email="bonjour@hotmail.com")

        self.assertFalse(PendingInvitation.get_organisation_pending_list(self.organisation))
        user2 = User.object.create_user(email="bonjour@hotmail.com", password="test12345")
        self.assertFalse(PendingInvitation.get_list_pending_invitation(user2))

        # todo test membership creation


class TestPlatformManagement(TestCase):
    def test_platform_management_get_or_create(self):
        self.assertFalse(PlatformManagement.objects.all())  # No objects
        platform_management = PlatformManagement.get_or_create()
        self.assertEqual(platform_management, PlatformManagement.objects.first())
        platform_management_2 = PlatformManagement.get_or_create()
        # Test that the method do not create a new object but get the existent one
        self.assertEqual(platform_management, platform_management_2)

    def test_platform_management_name(self):
        platform_management = PlatformManagement.get_or_create()
        self.assertEqual(str(platform_management), "Platform management")
