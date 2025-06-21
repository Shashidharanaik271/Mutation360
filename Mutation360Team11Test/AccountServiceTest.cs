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
    public void GetApplicationName_BlockRemoval_ReturnsEmptyString()
    {
        // Arrange
        var mockExternalService = new Mock<IExternalService>();
        mockExternalService.Setup(es => es.GetApplicationName()).Returns("TestApplicationName");
        var accountService = new AccountService(mockExternalService.Object);
        int validApplicationId = 1;

        // Act
        var result = accountService.GetApplicationName(validApplicationId);

        // Assert
        Assert.Equal("TestApplicationName", result);
    }

    [Fact]
    public void GetAllAccountDescription_ConditionalTrueMutation_ShouldReturnNullDescriptions_WhenCanProcessAccountDescriptionIsFalse()
    {
        // Arrange
        var accounts = new List<Account>
        {
            new Account { Id = 1, AccountName = "Account1", AccountDescription = "Description1", AccountType = AccountType.SystemAdmin },
            new Account { Id = 2, AccountName = "Account2", AccountDescription = "Description2", AccountType = AccountType.BusinessAdmin }
        };

        // Act
        var result = _accountService.GetAllAccountDescription(accounts, false);

        // Assert
        Assert.Equal(2, result.Count);
        Assert.Equal("Account1", result[0].AccountName);
        Assert.Null(result[0].AccountDescription);
        Assert.Equal("Account2", result[1].AccountName);
        Assert.Null(result[1].AccountDescription);
    }

    [Fact]
    public void GetAllAccountTypeAndDescription_ObjectInitializerMutation_SetsPropertiesCorrectly()
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
            }
        };

        // Act
        var result = _accountService.GetAllAccountTypeAndDescription(accounts);

        // Assert
        Assert.Single(result);
        Assert.Equal("Description1", result[0].AccountDescription);
        Assert.Equal(AccountType.SystemAdmin, result[0].AccountType);
    }

    [Fact]
    public void GetAccountKeySecondElement_ConditionalTrueMutation_ReturnsNullForNullAccountKey()
    {
        // Arrange
        string accountKey = null;

        // Act
        var result = _accountService.GetAccountKeySecondElement(accountKey);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void GetAccountKeySecondElement_NullAccountKey_ReturnsNull_ForFirstOrDefaultMutation()
    {
        // Arrange
        string accountKey = null;

        // Act
        var result = _accountService.GetAccountKeySecondElement(accountKey);

        // Assert
        Assert.Null(result);
    }

    [Theory]
    [InlineData("TestName", "TestDescription", null)]
    public void GetAccountIdByOtherInformationAsString_LogicalMutation_ThrowsException(string name, string description, string key)
    {
        // Act & Assert
        Assert.Throws<Exception>(() => _accountService.GetAccountIdByOtherInformationAsString(name, description, key));
    }

    [Theory]
    [InlineData("TestName", "", "TestKey")]
    public void GetAccountIdByOtherInformationAsString_LogicalMutation_ThrowsException(string name, string description, string key)
    {
        // Act & Assert
        Assert.Throws<Exception>(() => _accountService.GetAccountIdByOtherInformationAsString(name, description, key));
    }

    [Fact]
    public void GetAllAccount_NullCoalescing_ReturnsEmptyListWhenAccountsIsNull()
    {
        // Arrange
        List<Account> accounts = null;

        // Act
        var result = _accountService.GetAllAccount(accounts);

        // Assert
        Assert.Empty(result);
    }

    [Fact]
    public void GetAllAccount_NullCoalescingRemoval_ReturnsOriginalList()
    {
        // Arrange
        var accounts = new List<Account>
        {
            new Account { Id = 1, AccountName = "Account1", AccountDescription = "Description1", AccountType = AccountType.SystemAdmin, AccountKey = "Key1" },
            new Account { Id = 2, AccountName = "Account2", AccountDescription = "Description2", AccountType = AccountType.BusinessAdmin, AccountKey = "Key2" }
        };

        // Act
        var result = _accountService.GetAllAccount(accounts);

        // Assert
        Assert.Same(accounts, result);
    }

    [Fact]
    public void GetApplicationName_EqualityMutation_ApplicationIdIsOne_ReturnsEmptyString()
    {
        // Arrange
        var mockExternalService = new Mock<IExternalService>();
        var accountService = new AccountService(mockExternalService.Object);
        int applicationId = 1;

        // Act
        var result = accountService.GetApplicationName(applicationId);

        // Assert
        Assert.Equal(string.Empty, result);
    }
}
