from django.test import TestCase

from home.models import User, Organisation, Membership
from assessment.models import Assessment, Evaluation
from assessment.tests.object_creation import create_assessment_body, create_evaluation


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
        self.assertEqual(self.organisation.count_members(), 1)
        self.assertEqual(self.organisation.get_list_admin_members(), [member_user1])
        self.assertEqual(self.organisation.count_admin_members(), 1)
        self.assertEqual(self.organisation.get_membership_user(self.user1), member_user1)
        self.assertTrue(self.organisation.check_user_is_member(self.user1))
        self.assertTrue(self.organisation.check_user_is_member_as_admin(self.user1))
        self.assertEqual(self.organisation.get_role_user(self.user1), "admin")

    def test_user_membership(self):
        # Test if the user has membership in the organisation
        member_user1 = self.user1.membership_set.get(organisation=self.organisation)
        self.assertIn(member_user1, self.user1.get_list_all_memberships_user())
        self.assertFalse(self.user2.get_list_all_memberships_user())
        self.assertIn(self.organisation, self.user1.get_list_organisations_where_user_as_role(role="admin"))
        self.assertNotIn(self.organisation, self.user1.get_list_organisations_where_user_as_role(role="simple_user"))
        self.assertFalse(self.user2.get_list_organisations_where_user_as_role(role="admin"))

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
        self.organisation.add_user_to_organisation(user=self.user2, role="simple_user")
        self.assertIn(self.organisation, self.user2.get_list_organisations_where_user_as_role("simple_user"))
        member_user2 = self.user2.membership_set.get(organisation=self.organisation, user=self.user2)
        self.assertEqual(self.organisation.get_list_members_not_staff(), [member_user1, member_user2])
        self.assertIn(member_user2, self.user2.get_list_all_memberships_user())

    def test_organisation_two_members(self):
        # Add a user to the organisation and check that the organisation methods respond well
        self.organisation.add_user_to_organisation(user=self.user2, role="simple_user")
        member_user1 = self.user1.membership_set.get(organisation=self.organisation, user=self.user1)
        member_user2 = self.user2.membership_set.get(organisation=self.organisation, user=self.user2)
        self.assertEqual(self.organisation.get_list_members_not_staff(), [member_user1, member_user2])
        self.assertEqual(self.organisation.count_members(), 2)
        self.assertEqual(self.organisation.get_list_admin_members(), [member_user1])
        self.assertEqual(self.organisation.count_admin_members(), 1)
        self.assertEqual(self.organisation.get_membership_user(self.user1), member_user1)
        self.assertEqual(self.organisation.get_membership_user(self.user2), member_user2)
        # Security check: is the user belonging to the organisation ?
        self.assertTrue(self.organisation.check_user_is_member(self.user1))
        self.assertTrue(self.organisation.check_user_is_member_as_admin(self.user1))
        self.assertTrue(self.organisation.check_user_is_member(self.user2))
        self.assertFalse(self.organisation.check_user_is_member_as_admin(self.user2))
        self.assertEqual(self.organisation.get_role_user(self.user2), "simple_user")

    def test_organisation_remove_user(self):
        # Test removing a simple user in an organisation with 2 users
        self.organisation.add_user_to_organisation(user=self.user2, role="simple_user")
        self.assertIn(self.organisation, self.user2.get_list_organisations_where_user_as_role(role="simple_user"))
        self.assertTrue(self.organisation.check_user_is_member(self.user2))
        self.organisation.remove_user_to_organisation(self.user2)
        with self.assertRaises(Exception):
            self.user2.membership_set.get(organisation=self.organisation, user=self.user2)
        member_user1 = self.user1.membership_set.get(organisation=self.organisation, user=self.user1)
        self.assertEqual(self.organisation.get_list_members_not_staff(), [member_user1])
        self.assertFalse(self.organisation.check_user_is_member(self.user2))

    def test_organisation_remove_user_bis(self):
        # Test that the user is not removed when it is the last one in the organisation
        self.assertEqual(self.organisation.count_members(), 1)
        self.organisation.remove_user_to_organisation(user=self.user1)
        self.assertEqual(self.organisation.count_members(), 1)
        self.assertTrue(self.organisation.check_user_is_member_as_admin(self.user1))

    def test_organisation_add_already_member(self):
        # Test that the user is not added to the organisation because he is already a member
        self.assertEqual(self.organisation.count_members(), 1)
        self.organisation.add_user_to_organisation(user=self.user1, role="simple_user")
        self.assertEqual(self.organisation.count_members(), 1)
        self.assertTrue(self.organisation.check_user_is_member_as_admin(self.user1))

    def test_organisation_deletion_and_members(self):
        self.organisation.delete()
        with self.assertRaises(Exception):
            Membership.objects.get(user=self.user1)
        self.assertFalse(self.user1.get_list_all_memberships_user())  # User1 has no longer a membership
        # Todo test the view which deletes the organisation (and create it)


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
