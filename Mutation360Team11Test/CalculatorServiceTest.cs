using Mutation360Team11.Services;

namespace Mutation360Team11Test;

public class CalculatorServiceTest
{
	private readonly CalculatorService _calculatorService;

	public CalculatorServiceTest()
	{
		_calculatorService = new CalculatorService();
	}

	[Theory]
	//[InlineData(3, 5, 8)]
	//[InlineData(10, 20, 30)]
	//[InlineData(-4, 6, 2)]
	[InlineData(0, 0, 0)]
	public void Add_ShouldReturnCorrectSum(double a, double b, double expected)
	{
		// Act
		var result = _calculatorService.Add(a, b);

		// Assert
		Assert.Equal(expected, result);
	}

	[Theory]
	//[InlineData(3, 5, -2)]
	//[InlineData(10, 20, -20)]
	//[InlineData(-4, 6, 10)]
	//[InlineData(14, 6, 8)]
	[InlineData(0, 0, 0)]
	public void Subtract_ShouldReturnCorrectDifference(double a, double b, double expected)
	{
		// Act
		var result = _calculatorService.Subtract(a, b);

		// Assert
		Assert.Equal(expected, result);
	}

	[Theory]
	//[InlineData(3, 5, 15)]
	//[InlineData(-4, 6, -24)]
	[InlineData(1, 1, 1)]
	public void Multiply_ShouldReturnCorrectProduct(double a, double b, double expected)
	{
		// Act
		var result = _calculatorService.Multiply(a, b);

		// Assert
		Assert.Equal(expected, result);
	}

	[Theory]
	//[InlineData(30, 5, 6)]
	//[InlineData(-24, 6, -4)]
	[InlineData(0, 20, 0)]
	//[InlineData(0, 0, 0)]
	public void Divide_ShouldReturnCorrectQuotient(double a, double b, double expected)
	{
		// Act
		var result = _calculatorService.Divide(a, b);

		// Assert
		Assert.Equal(expected, result);
	}

	//[Fact]
	//public void Divide_ShouldThrowDivideByZeroException_WhenDivisorIsZero()
	//{
	//	// Act & Assert
	//	Assert.Throws<DivideByZeroException>(() => _calculatorService.Divide(10, 0));
	//}

    [Fact]
    public void Add_TwoPositiveNumbers_ReturnsCorrectSum()
    {
        // Arrange
        double a = 5;
        double b = 3;
        double expected = 8;

        // Act
        var result = _calculatorService.Add(a, b);

        // Assert
        Assert.Equal(expected, result);
    }

    [Fact]
    public void Subtract_ShouldSubtractPositiveNumbers()
    {
        // Arrange
        var a = 10;
        var b = 5;
        var expected = 5;

        // Act
        var result = _calculatorService.Subtract(a, b);

        // Assert
        Assert.Equal(expected, result);
    }

    [Fact]
    public void Multiply_ShouldReturnCorrectProduct_WhenOperandsAreNonZero()
    {
        // Arrange
        var a = 4;
        var b = 2;
        var expected = 8;

        // Act
        var result = _calculatorService.Multiply(a, b);

        // Assert
        Assert.Equal(expected, result);
    }

    [Fact]
    public void Divide_ShouldReturnCorrectQuotient_WithNonZeroOperands()
    {
        // Arrange
        double a = 10;
        double b = 2;
        double expected = 5;

        // Act
        var result = _calculatorService.Divide(a, b);

        // Assert
        Assert.Equal(expected, result);
    }
}
