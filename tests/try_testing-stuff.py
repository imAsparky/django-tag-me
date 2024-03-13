from hypothesis import given, strategies as st


#
#
# def valid_tag_dictionaries(min_size=1):
#     """
#     Generates non-empty dictionaries with a 'tags' key, ensuring a minimum
#     number of key-value pairs.
#
#     :param min_size: The minimum number of key-value pairs in the generated dictionaries.
#                      (Defaults to 1).
#
#     :returns: A Hypothesis strategy that generates valid tag dictionaries.
#     """
#
#     return st.dictionaries(
#         keys=st.just("tags"), values=st.text(min_size=1), min_size=min_size
#     ).filter(lambda d: d)
#
#
# @given(valid_tag_dictionaries())
# @given(
#     st.dictionaries(
#         keys=st.just("tags"),
#         values=st.one_of(
#             st.integers(),
#             st.floats(),
#             st.booleans(),
#             st.lists(st.integers(), min_size=1, max_size=2),
#             st.lists(st.floats(), min_size=1, max_size=2),
#             st.lists(st.booleans(), min_size=1, max_size=2),
#         ),
#     ).filter(
#         lambda tags: tags != {}
#     )  # Filter out empty 'tags'
# )
# def test_min_size(tags):
#     print(f"TAGS: {repr(tags)}")
#     # assert 1 == 2
#
#
import re

error_message = 'An invalid dictionary was passed %s ["{'tags': 0} The dict must contain a value type str or set[str] or list[str]. Keys supplied dict_keys(['tags']). Value type <class 'int'>."]'
error_pattern = re.compile(r"An invalid dictionary was passed (.*)")
match = re.search(error_pattern, error_message)

if match:
    captured_text = match.group(0) + match.group(
        1
    )  # Access the text after the initial message
    print(captured_text)

if __name__ == "__main__":

    """
    # test_min_size()
    #
    # # @given(
    # #     st.text(min_size=1),
    # # )


    # @mock.patch(
    #         "tag_me.utils.collections._extract_tags_from_dict.logger"
    #     )  # Replace 'your_module' with the correct module name
    #     def test_logging_on_error(self, mock_logger):
    #         print(f"MOCK LOGGER {mock_logger}")
    #         invalid_tags = {"tags": 123}  # Example of an invalid dictionary
    #         with self.assertRaises(ValidationError):
    #             self.formatter._extract_tags_from_dict(invalid_tags)
    #
    #         # Assert that the logger was called with the expected message
    #         mock_logger.error.assert_called_with(
    #             "An invalid dictionary was passed "
    #         )
    """
