from openfisca_uk.model_api import *
import pandas as pd


class person_id(Variable):
    value_type = int
    entity = Person
    label = "ID for the person"
    definition_period = YEAR


class people(Variable):
    value_type = float
    entity = Person
    label = "Variable holding people"
    definition_period = YEAR
    default_value = 1


class raw_person_weight(Variable):
    value_type = float
    entity = Person
    label = "Weight factor"
    documentation = "Used to translate from survey respondents to UK residents"
    definition_period = YEAR
    default_value = 1


class person_weight(Variable):
    value_type = float
    entity = Person
    label = "Weight (region-adjusted)"
    documentation = "Adjusted to match regional population estimates"
    definition_period = YEAR

    def formula(person, period, parameters):
        nation = person.household("country", period)
        frs_person_weight = person("raw_person_weight", period)
        national_population = parameters(
            period
        ).demographic.population_estimate[nation]
        national_weight_sum = (
            pd.Series(frs_person_weight).groupby(nation).sum()[nation]
        )
        scale_factor = national_population / national_weight_sum
        return scale_factor * frs_person_weight


class age(Variable):
    value_type = int
    entity = Person
    label = "Age"
    unit = "year"
    documentation = "The age of the person in years"
    definition_period = YEAR
    quantity_type = STOCK

    def formula(person, period, parameters):
        ADULT_DEFAULT_AGE = 18
        CHILD_DEFAULT_AGE = 10
        is_adult = person.benunit.members_role == BenUnit.ADULT
        return where(is_adult, ADULT_DEFAULT_AGE, CHILD_DEFAULT_AGE)


class birth_year(Variable):
    value_type = int
    entity = Person
    label = "The birth year of the person"
    definition_period = YEAR

    def formula(person, period, parameters):
        return period.start.year - person("age", period)


class over_16(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is over 16"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) >= 16


class is_adult(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is an adult"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) >= 18


class is_child(Variable):
    value_type = bool
    entity = Person
    label = "Is a child"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) < 18


class child_index(Variable):
    value_type = int
    entity = Person
    label = "Child reference number"
    definition_period = YEAR

    def formula(person, period, parameters):
        # The child index, by age, descending (e.g. "first child" = 1)
        child_ranking = (
            person.get_rank(
                person.benunit,
                -person("age", period),
                condition=person("is_child", period),
            )
            + 1
        )
        # Fill in adult values
        return where(person("is_child", period), child_ranking, 100)


class is_eldest_child(Variable):
    label = "Is the eldest child"
    documentation = (
        "Whether this person is the eldest child in the benefit unit"
    )
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        return person("child_index", period) == 1


class is_benunit_eldest_child(Variable):
    value_type = bool
    entity = Person
    label = "Eldest child in the benefit unit"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        is_child = person("is_child", period)
        eldest_age = person.benunit("eldest_child_age", period)
        age_tie = person.benunit.sum((age == eldest_age) & is_child) > 1
        is_eldest_age = person("age", period) == eldest_age
        child_id = person("person_id", period) * is_child
        max_child_id = person.benunit.max(child_id)
        has_max_child_id = child_id == max_child_id
        return where(is_eldest_age & age_tie, has_max_child_id, is_eldest_age)


class MaritalStatus(Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    SEPARATED = "Separated"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"


class marital_status(Variable):
    value_type = Enum
    possible_values = MaritalStatus
    default_value = MaritalStatus.SINGLE
    entity = Person
    label = "Marital status"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return where(
            person.benunit("is_married", period),
            MaritalStatus.MARRIED,
            MaritalStatus.SINGLE,
        )


class EducationType(Enum):
    NOT_IN_EDUCATION = "Not in education"
    PRE_PRIMARY = "Pre-primary"
    NOT_COMPLETED_PRIMARY = "Not completed primary"
    PRIMARY = "Primary"
    LOWER_SECONDARY = "Lower Secondary"
    UPPER_SECONDARY = "Upper Secondary"
    POST_SECONDARY = "Post Secondary"
    TERTIARY = "Tertiary"


class current_education(Variable):
    value_type = Enum
    possible_values = EducationType
    default_value = EducationType.NOT_IN_EDUCATION
    entity = Person
    label = "Current education"
    definition_period = YEAR


class highest_education(Variable):
    value_type = Enum
    possible_values = EducationType
    default_value = EducationType.UPPER_SECONDARY
    entity = Person
    label = "Highest status education completed"
    definition_period = YEAR


class in_FE(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is in Further Education"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period


class in_HE(Variable):
    value_type = bool
    entity = Person
    label = "In higher education"
    definition_period = YEAR
    reference = "Whether this person is in Higher Education"
    set_input = set_input_dispatch_by_period


class Gender(Enum):
    MALE = "Male"
    FEMALE = "Female"


class gender(Variable):
    value_type = Enum
    possible_values = Gender
    default_value = Gender.MALE
    entity = Person
    label = "Gender of the person"
    definition_period = ETERNITY


class is_male(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is male"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("gender", period) == Gender.MALE


class is_female(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is female"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("gender", period) == Gender.FEMALE


class is_household_head(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is the head-of-household"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person.get_rank(person.household, person("age", period)) == 0


class is_benunit_head(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is the head-of-family"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person.get_rank(person.benunit, person("age", period)) == 0


class in_social_housing(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person lives in social housing"
    definition_period = YEAR

    def formula(person, period, parameters):
        tenure = person.household("tenure_type", period.this_year)
        tenures = tenure.possible_values
        return is_in(tenure, tenures.RENT_FROM_COUNCIL, tenures.RENT_FROM_HA)


class is_WA_adult(Variable):
    value_type = bool
    entity = Person
    label = "Whether is a working-age adult"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("is_adult", period) & ~person("is_SP_age", period)


class is_young_child(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is under 14"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) < 14


class age_under_18(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is under age 18"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) < 18


class age_18_64(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is age 18 to 64"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        return (age >= 18) & (age <= 64)


class age_over_64(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is over age 64"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) > 64


class is_older_child(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is over 14 but under 18"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        return (age >= 14) & (age < 18)
