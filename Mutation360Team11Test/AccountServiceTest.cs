using Moq;
using Mutation360Team11.Enums;
using Mutation360Team11.Models;
using Mutation360Team11.Services;

namespace Mutation360Team11Test;

public class AccountServiceTest
{
	private readonly Mock<IExternalService> _mockExternalServiceMock;
	private readonly AccountService _accountService;

	public AccountServiceTest()
	{
		_mockExternalServiceMock = new Mock<IExternalService>();
		_accountService = new AccountService(_mockExternalServiceMock.Object);
	}

	[Fact]
	public void GetAllAccountDescription_ShouldReturnCorrectAccountDetails_WhenCanProcessAccountDescriptionIsTrue()
	{
		// Arrange
		var accounts = new List<Account>
			{
				new Account { Id = 1, AccountName = "Account1", AccountDescription = "Description1", AccountType = AccountType.SystemAdmin },
				new Account { Id = 2, AccountName = "Account2", AccountDescription = "Description2", AccountType = AccountType.BusinessAdmin }
			};

		// Act
		var result = _accountService.GetAllAccountDescription(accounts, true);

		// Assert
		Assert.Equal(2, result.Count);
		Assert.Equal("Account1", result[0].AccountName);
		Assert.Equal("Description1", result[0].AccountDescription);
		Assert.Equal("Account2", result[1].AccountName);
		Assert.Equal("Description2", result[1].AccountDescription);
	}

	//[Fact]
	//public void GetAllAccountDescription_ShouldReturnNullDescriptions_WhenCanProcessAccountDescriptionIsFalse()
	//{
	//	// Arrange
	//	var accounts = new List<Account>
	//	{
	//		new Account { Id = 1, AccountName = "Account1", AccountDescription = "Description1", AccountType = AccountType.SystemAdmin },
	//		new Account { Id = 2, AccountName = "Account2", AccountDescription = "Description2", AccountType = AccountType.BusinessAdmin }
	//	};

	//	// Act
	//	var result = _accountService.GetAllAccountDescription(accounts, false);

	//	// Assert
	//	Assert.Equal(2, result.Count);
	//	Assert.Equal("Account1", result[0].AccountName);
	//	Assert.Null(result[0].AccountDescription);
	//	Assert.Equal("Account2", result[1].AccountName);
	//	Assert.Null(result[1].AccountDescription);
	//}

	[Fact]
	public void GetAllAccountTypeAndDescription_ShouldReturnCorrectDetails()
	{
		// Arrange
		var accounts = new List<Account>
		{
			new Account
			{
				Id = 1,
				AccountName = "Account1",
				AccountDescription = "Description1",
				AccountType = AccountType.SystemAdmin,
				AccountKey = null!
			},
			new Account
			{
				Id = 2,
				AccountName = "Account2",
				AccountDescription = "Description2",
				AccountType = AccountType.BusinessAdmin,
				AccountKey = "2:Account2Key"
			}
		};

		// Act
		var result = _accountService.GetAllAccountTypeAndDescription(accounts);

		// Assert
		Assert.NotNull(result);
		//Assert.Equal(2, result.Count);

		//Assert.Equal("Description1", result[0].AccountDescription);
		//Assert.Equal(AccountType.SystemAdmin, result[0].AccountType);

		//Assert.Equal("Description2", result[1].AccountDescription);
		//Assert.Equal(AccountType.BusinessAdmin, result[1].AccountType);
	}

	[Fact]
	public void GetAccountKeyFirstElement_ValidAccountKey_ReturnsFirstElement()
	{
		// Arrange
		string accountKey = "part1:part2:part3";

		// Act
		var result = _accountService.GetAccountKeySecondElement(accountKey);

		// Assert
		Assert.Equal("part2", result);
	}

	//[Fact]
	//public void GetAccountKeyFirstElement_EmptyAccountKey_ThrowsException()
	//{
	//	// Arrange
	//	string accountKey = "";

	//	// Act & Assert
	//	Assert.Throws<InvalidOperationException>(() => _accountService.GetAccountKeySecondElement(accountKey));
	//}

	//[Fact]
	//public void GetAccountKeyFirstElement_NullAccountKey_ThrowsException()
	//{
	//	// Arrange
	//	string accountKey = null!;

	//	// Act
	//	var result = _accountService.GetAccountKeySecondElement(accountKey);

	//	// Assert
	//	Assert.Equal(accountKey, result);
	//}

	//[Fact]
	//public void GetAccountKeyFirstElement_InvalidFormatAccountKey_ThrowsException()
	//{
	//	// Arrange
	//	string accountKey = "singlePart";

	//	// Act & Assert
	//	Assert.Throws<InvalidOperationException>(() => _accountService.GetAccountKeySecondElement(accountKey));
	//}

	[Fact]
	public void GetAccountIdByOtherInformationAsString_ValidInputs_ReturnsGuidString()
	{
		// Arrange
		string name = "TestName";
		string description = "TestDescription";
		string key = "TestKey";

		// Act
		var result = _accountService.GetAccountIdByOtherInformationAsString(name, description, key);

		// Assert
		Assert.False(string.IsNullOrWhiteSpace(result));
		Assert.True(Guid.TryParse(result, out _));
	}

	[Theory]
	//[InlineData(null, "TestDescription", "TestKey")]
	//[InlineData("TestName", null, "TestKey")]
	//[InlineData("TestName", "TestDescription", null)]
	//[InlineData("", "TestDescription", "TestKey")]
	//[InlineData("TestName", "", "TestKey")]
	//[InlineData("TestName", "TestDescription", "")]
	[InlineData("", "", "")]
	public void GetAccountIdByOtherInformationAsString_InvalidInputs_ThrowsException(string name, string description, string key)
	{
		// Arrange
		// Act & Assert
		Assert.Throws<Exception>(() => _accountService.GetAccountIdByOtherInformationAsString(name, description, key));
	}

	//[Fact]
	//public void GetAllAccount_ShouldReturnSameList_WhenAccountsIsNotNull()
	//{
	//	// Arrange
	//	var accounts = new List<Account>
	//	{
	//		new Account { Id = 1, AccountName = "Account1", AccountDescription = "Description1", AccountType = AccountType.SystemAdmin, AccountKey = "Key1" },
	//		new Account { Id = 2, AccountName = "Account2", AccountDescription = "Description2", AccountType = AccountType.BusinessAdmin, AccountKey = "Key2" }
	//	};

	//	// Act
	//	var result = _accountService.GetAllAccount(accounts);

	//	// Assert
	//	Assert.Equal(accounts, result);
	//}

	[Fact]
	public void GetAllAccount_ShouldReturnEmptyList_WhenAccountsIsNull()
	{
		// Arrange
		List<Account> accounts = null;

		// Act
		var result = _accountService.GetAllAccount(accounts);

		// Assert
		Assert.NotNull(result);
		Assert.Empty(result);
	}

	//[Fact]
	//public void GetApplicationName_ValidApplicationId_ReturnsApplicationName()
	//{
	//	// Arrange
	//	var mockExternalService = new Mock<IExternalService>();
	//	mockExternalService.Setup(es => es.GetApplicationName()).Returns("TestApplicationName");
	//	var accountService = new AccountService(mockExternalService.Object);
	//	int validApplicationId = 1;

	//	// Act
	//	var result = accountService.GetApplicationName(validApplicationId);

	//	// Assert
	//	Assert.Equal("TestApplicationName", result);
	//	mockExternalService.Verify(es => es.GetApplicationName(), Times.Once);
	//}

	[Fact]
	public void GetApplicationName_InvalidApplicationId_ReturnsEmptyString()
	{
		// Arrange
		var mockExternalService = new Mock<IExternalService>();
		var accountService = new AccountService(mockExternalService.Object);
		int invalidApplicationId = 0;

		// Act
		var result = accountService.GetApplicationName(invalidApplicationId);

		// Assert
		Assert.Equal(string.Empty, result);
	}

    [Fact]
            public void GetApplicationName_ConstructorBlockRemoved_ThrowsNullReferenceOnValidId()
            {
                // Arrange
                _mockExternalServiceMock.Setup(s => s.GetApplicationName()).Returns("SomeAppName");
                var validApplicationId = 1;

                // Act
                var result = _accountService.GetApplicationName(validApplicationId);

                // Assert
                // This assertion will pass with the original code, but the method call will
                // throw a NullReferenceException with the mutated code, killing the mutant.
                Assert.Equal("SomeAppName", result);
            }

    [Fact]
    public void GetAllAccountDescription_WhenConditionalIsTrueMutationAndCanProcessIsFalse_ReturnsNullDescription()
    {
        // Arrange
        var accounts = new List<Account>
        {
            new Account { Id = 1, AccountName = "Account1", AccountDescription = "Description1", AccountType = AccountType.SystemAdmin }
        };

        // Act
        var result = _accountService.GetAllAccountDescription(accounts, false);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Null(result[0].AccountDescription);
    }

    [Fact]
    public void GetAllAccountTypeAndDescription_ObjectInitializerMutation_ReturnsCorrectlyMappedDetails()
    {
        // Arrange
        var accounts = new List<Account>
        {
            new Account
            {
                Id = 1,
                AccountName = "Test Account",
                AccountDescription = "Specific Description",
                AccountType = AccountType.BusinessAdmin // A non-default enum value
            }
        };

        // Act
        var result = _accountService.GetAllAccountTypeAndDescription(accounts);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        var details = result.First();
        Assert.Equal("Specific Description", details.AccountDescription);
        Assert.Equal(AccountType.BusinessAdmin, details.AccountType);
    }

    [Fact]
    public void GetAccountKeySecondElement_WhenAccountKeyIsNull_ReturnsNull()
    {
        // Arrange
        string accountKey = null;

        // Act
        var result = _accountService.GetAccountKeySecondElement(accountKey);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    	public void GetAccountKeySecondElement_LinqFirstToFirstOrDefault_ThrowsExceptionWhenKeyHasNoDelimiter()
    	{
    		// Arrange
    		var accountKey = "singlepart";

    		// Act & Assert
    		Assert.Throws<InvalidOperationException>(() => _accountService.GetAccountKeySecondElement(accountKey));
    	}

    [Fact]
    public void GetAccountIdByOtherInformationAsString_LogicalMutation_ThrowsExceptionWhenOnlyDescriptionIsInvalid()
    {
        // Arrange
        var name = "ValidName";
        var description = ""; // Invalid
        var key = "ValidKey";

        // Act & Assert
        Assert.Throws<Exception>(() => _accountService.GetAccountIdByOtherInformationAsString(name, description, key));
    }

    [Fact]
            public void GetAccountIdByOtherInformationAsString_LogicalMutation_ThrowsExceptionWhenOnlyOneArgumentIsInvalid()
            {
                // Arrange
                var name = "ValidName";
                var description = "ValidDescription";
                var key = ""; // Invalid key

                // Act & Assert
                Assert.Throws<Exception>(() => _accountService.GetAccountIdByOtherInformationAsString(name, description, key));
            }

    [Fact]
            public void GetAllAccount_NullCoalescingMutation_ReturnsSameListWhenNotNull()
            {
                // Arrange
                var accounts = new List<Account>
                {
                    new Account { Id = 1, AccountName = "Account1" }
                };

                // Act
                var result = _accountService.GetAllAccount(accounts);

                // Assert
                Assert.Same(accounts, result);
            }

    [Fact]
        public void GetAllAccount_NullCoalescingRemoveLeft_ReturnsInputListWhenNotNull()
        {
            // Arrange
            var accounts = new List<Account>
            {
                new Account { Id = 1, AccountName = "Test Account" }
            };

            // Act
            var result = _accountService.GetAllAccount(accounts);

            // Assert
            Assert.Same(accounts, result);
        }

    [Fact]
    public void GetApplicationName_EqualityMutation_ReturnsApplicationNameWhenIdIsOne()
    {
        // Arrange
        var expectedAppName = "TestApplication";
        _mockExternalServiceMock.Setup(es => es.GetApplicationName()).Returns(expectedAppName);
        var accountService = new AccountService(_mockExternalServiceMock.Object);
        int applicationId = 1;

        // Act
        var result = accountService.GetApplicationName(applicationId);

        // Assert
        Assert.Equal(expectedAppName, result);
    }
}
